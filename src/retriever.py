"""Deterministic hybrid retriever for BIS standards."""

from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "data" / "index" / "standards.json"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "bis",
    "bureau",
    "by",
    "can",
    "company",
    "comply",
    "compliance",
    "cover",
    "covered",
    "covers",
    "detailing",
    "details",
    "for",
    "from",
    "governs",
    "i",
    "in",
    "india",
    "indian",
    "intended",
    "is",
    "looking",
    "manufacture",
    "manufactured",
    "manufacturing",
    "need",
    "of",
    "official",
    "on",
    "or",
    "our",
    "product",
    "products",
    "regulation",
    "regulations",
    "requirement",
    "requirements",
    "small",
    "standard",
    "standards",
    "the",
    "their",
    "this",
    "to",
    "use",
    "used",
    "we",
    "what",
    "which",
    "with",
    "without",
}

NORMALISATIONS = {
    "autocalved": "autoclaved",
    "autoclave": "autoclaved",
    "masonry": "masonry",
    "mansory": "masonry",
    "pozzolanic": "pozzolana",
    "pozzolona": "pozzolana",
    "supersulphated": "supersulphated",
    "sulphated": "sulphated",
    "reinforcements": "reinforcement",
    "reinforced": "reinforced",
    "unreinforced": "unreinforced",
    "cladding": "cladding",
}


def _stem(token: str) -> str:
    if token in NORMALISATIONS:
        return NORMALISATIONS[token]
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 6 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 5 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = text.replace("pozzolana", "pozzolana")
    text = text.replace("fly-ash", "fly ash")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = []
    for token in text.split():
        if len(token) <= 1 or token in STOPWORDS:
            continue
        tokens.append(_stem(token))
    return tokens


def normalized_text(text: str) -> str:
    return " ".join(tokenize(text))


def normalized_standard_id(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def standard_numbers(value: str) -> set[str]:
    return set(re.findall(r"\b\d{2,5}[a-z]?\b", value.lower()))


class StandardsRetriever:
    def __init__(self, index_path: Path = DEFAULT_INDEX):
        with index_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        self.records: list[dict[str, Any]] = payload["standards"]
        self.doc_tokens: list[list[str]] = []
        self.title_tokens: list[list[str]] = []
        document_frequency: Counter[str] = Counter()

        for record in self.records:
            title = str(record.get("title", ""))
            scope = str(record.get("scope", ""))
            text = str(record.get("text", ""))
            search_text = " ".join(
                [
                    str(record["standard_id"]),
                    title,
                    title,
                    title,
                    scope,
                    scope,
                    text,
                ]
            )
            tokens = tokenize(search_text)
            self.doc_tokens.append(tokens)
            self.title_tokens.append(tokenize(title))
            document_frequency.update(set(tokens))

        self.document_count = len(self.records)
        self.average_length = sum(len(tokens) for tokens in self.doc_tokens) / max(
            self.document_count, 1
        )
        self.idf = {
            term: math.log(
                1
                + (self.document_count - frequency + 0.5) / (frequency + 0.5)
            )
            for term, frequency in document_frequency.items()
        }

    def _bm25(self, query_tokens: list[str], doc_index: int) -> float:
        term_frequency = Counter(self.doc_tokens[doc_index])
        query_frequency = Counter(query_tokens)
        document_length = len(self.doc_tokens[doc_index])
        k1 = 1.55
        b = 0.72
        score = 0.0

        for term, q_count in query_frequency.items():
            frequency = term_frequency.get(term, 0)
            if not frequency:
                continue
            denominator = frequency + k1 * (
                1 - b + b * document_length / self.average_length
            )
            score += (
                self.idf.get(term, 0.0)
                * (frequency * (k1 + 1))
                / denominator
                * (1 + 0.18 * (q_count - 1))
            )
        return score

    def _heuristic_boost(
        self, query: str, query_tokens: list[str], doc_index: int
    ) -> tuple[float, list[str]]:
        record = self.records[doc_index]
        standard_id = str(record["standard_id"])
        title = str(record.get("title", ""))
        title_tokens = self.title_tokens[doc_index]
        title_set = set(title_tokens)
        query_set = set(query_tokens)
        query_norm = normalized_text(query)
        title_norm = normalized_text(title)
        reasons: list[str] = []
        boost = 0.0

        if normalized_standard_id(standard_id) in normalized_standard_id(query):
            boost += 45.0
            reasons.append("standard id mentioned directly")

        query_numbers = standard_numbers(query)
        id_numbers = standard_numbers(standard_id)
        if query_numbers and query_numbers & id_numbers:
            boost += 12.0
            reasons.append("standard number matched")

        if title_tokens:
            overlap = title_set & query_set
            coverage = len(overlap) / len(title_set)
            boost += 10.0 * coverage
            rare_overlap = sum(self.idf.get(term, 0.0) for term in overlap)
            boost += 0.9 * rare_overlap
            if coverage >= 0.65:
                reasons.append("strong title term coverage")
            elif overlap:
                reasons.append("title terms overlap")

        if title_norm and title_norm in query_norm:
            boost += 24.0
            reasons.append("title phrase matched")

        # Reward distinctive adjacent title phrases found in the query.
        for width, weight in ((4, 12.0), (3, 8.0), (2, 4.0)):
            seen_phrases: set[str] = set()
            for index in range(0, max(len(title_tokens) - width + 1, 0)):
                phrase = " ".join(title_tokens[index : index + width])
                if phrase in seen_phrases:
                    continue
                seen_phrases.add(phrase)
                if phrase and phrase in query_norm:
                    boost += weight
                    reasons.append(f"{width}-term title phrase matched")
                    break

        cement_types = {
            "ordinary portland cement": 16.0,
            "portland slag cement": 18.0,
            "portland pozzolana cement": 16.0,
            "white portland cement": 20.0,
            "rapid harden portland cement": 16.0,
            "hydrophobic portland cement": 18.0,
            "sulphate resist portland cement": 18.0,
            "masonry cement": 18.0,
            "supersulphated cement": 22.0,
            "high alumina cement": 18.0,
        }
        for phrase, weight in cement_types.items():
            if phrase in query_norm and phrase in title_norm:
                boost += weight
                reasons.append("cement type matched")

        for grade in re.findall(r"\b(33|43|53)\s*grade\b", query.lower()):
            if grade in title.lower():
                boost += 10.0
                reasons.append(f"{grade} grade matched")

        product_phrases = {
            "coarse fine aggregate": 14.0,
            "precast concrete pipe": 16.0,
            "lightweight concrete block": 16.0,
            "hollow solid lightweight": 16.0,
            "asbestos cement sheet": 14.0,
            "roof cladding": 8.0,
            "water main": 7.0,
            "fly ash": 8.0,
            "calcined clay": 10.0,
        }
        for phrase, weight in product_phrases.items():
            if phrase in query_norm and phrase in title_norm + " " + normalized_text(str(record.get("scope", ""))):
                boost += weight
                reasons.append("product phrase matched")

        return boost, reasons

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_tokens = tokenize(query)
        scored: list[tuple[float, dict[str, Any], list[str]]] = []

        for index, record in enumerate(self.records):
            bm25_score = self._bm25(query_tokens, index)
            boost, reasons = self._heuristic_boost(query, query_tokens, index)
            score = bm25_score + boost
            if score <= 0:
                continue
            scored.append((score, record, reasons))

        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, record, reasons in scored[:top_k]:
            title = str(record.get("title", "")).title()
            if not reasons:
                reasons = ["matched terms in the SP 21 summary"]
            results.append(
                {
                    "standard_id": record["standard_id"],
                    "title": title,
                    "score": round(score, 4),
                    "rationale": f"{record['standard_id']} - {title}: {', '.join(dict.fromkeys(reasons))}.",
                    "pages": record.get("pages", []),
                }
            )
        return results

    def recommend(self, query: str, top_k: int = 5) -> tuple[list[dict[str, Any]], float]:
        start = time.perf_counter()
        results = self.search(query, top_k=top_k)
        latency = time.perf_counter() - start
        return results, latency


def load_retriever(index_path: Path = DEFAULT_INDEX) -> StandardsRetriever:
    return StandardsRetriever(index_path=index_path)

