"""Build a searchable standards index from the BIS SP 21 PDF dataset."""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "data" / "raw" / "dataset.pdf"
DEFAULT_OUTPUT = ROOT / "data" / "index" / "standards.json"

ROMAN = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
}

PART_PATTERN = (
    r"(?:\(\s*PART\s*([0-9IVXLCDM]+)\s*"
    r"(?:/\s*SEC(?:TION)?\s*([0-9IVXLCDM]+))?\s*\))?"
)
STANDARD_PATTERN = re.compile(
    r"IS\s*:?\s*([0-9]+[A-Z]?)\s*"
    + PART_PATTERN
    + r"\s*[:\-]?\s*(\d{4})",
    re.IGNORECASE,
)
SUMMARY_PATTERN = re.compile(r"SUMMARY\s+OF\s+\n?\s*IS\s*:?\s*", re.IGNORECASE)


def _normalise_part(part: str | None) -> str | None:
    if not part:
        return None
    upper = part.upper()
    return str(ROMAN.get(upper, upper))


def canonical_standard(match: re.Match[str]) -> str:
    """Return the evaluator-friendly display form for an Indian Standard ID."""

    number, part, section, year = match.groups()
    standard = f"IS {number.upper()}"
    if part:
        standard += f" (Part {_normalise_part(part)}"
        if section:
            standard += f"/Sec {_normalise_part(section)}"
        standard += f"): {year}"
    else:
        standard += f": {year}"
    return standard


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\uf0b1", " ")
    text = text.replace("±", " plus minus ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_title(segment: str) -> str:
    """Extract the heading title immediately following SUMMARY OF."""

    lines = [line.strip() for line in segment.splitlines() if line.strip()]
    title_lines: list[str] = []
    id_seen = False

    for line in lines[:18]:
        if re.search(r"SUMMARY\s+OF", line, re.IGNORECASE):
            continue

        if not id_seen and STANDARD_PATTERN.search(line):
            id_seen = True
            title_part = STANDARD_PATTERN.sub("", line).strip(" :-–—")
            if title_part:
                title_lines.append(title_part)
            continue

        if id_seen:
            if re.match(
                r"^\(?\s*(first|second|third|fourth|fifth|sixth|seventh|"
                r"eighth|ninth|tenth|revision)",
                line,
                re.IGNORECASE,
            ):
                break
            if re.match(r"^(\d+\.|TABLE|Note\b|For detailed)", line, re.IGNORECASE):
                break
            if len(title_lines) >= 5:
                break
            title_lines.append(line.strip(" -–—"))

    title = clean_text(" ".join(title_lines))
    title = re.sub(r"\bAUTOCLA\s+VED\b", "AUTOCLAVED", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*/\s*", "/", title)
    return title


def extract_scope(segment: str) -> str:
    """Pull the first scope paragraph when available."""

    compact = clean_text(segment)
    match = re.search(
        r"(?:1\.\s*)?Scope\s*[—\-–:]?\s*(.*?)(?=\s+[2-5]\.\s+[A-Z]|\s+TABLE\s+1|\s+Note\s+[—\-–]|$)",
        compact,
        re.IGNORECASE,
    )
    if not match:
        return ""
    return clean_text(match.group(1))[:900]


def extract_source_pages(segment: str, start_page: int | None = None) -> list[int]:
    pages = sorted({int(value) for value in re.findall(r"\[\[PAGE\s+(\d+)\]\]", segment)})
    if start_page is not None:
        pages = sorted(set([start_page] + pages))
    return pages[:8]


def iter_segments(reader: PdfReader) -> Iterable[tuple[str, int | None]]:
    page_texts = []
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_texts.append(f"\n\n[[PAGE {page_index}]]\n{page_text}")

    full_text = "\n".join(page_texts)
    starts = [match.start() for match in SUMMARY_PATTERN.finditer(full_text)]
    page_markers = [
        (match.start(), int(match.group(1)))
        for match in re.finditer(r"\[\[PAGE\s+(\d+)\]\]", full_text)
    ]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(full_text)
        start_page = None
        for marker_position, marker_page in page_markers:
            if marker_position > start:
                break
            start_page = marker_page
        yield full_text[start:end], start_page


def parse_standards(pdf_path: Path) -> list[dict[str, object]]:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(str(pdf_path))
    records: dict[str, dict[str, object]] = {}

    for segment, start_page in iter_segments(reader):
        heading = segment[:900].replace("\n", " ")
        match = STANDARD_PATTERN.search(heading)
        if not match:
            continue

        standard_id = canonical_standard(match)
        title = extract_title(segment)
        scope = extract_scope(segment)
        body = clean_text(segment)
        body = re.sub(r"\[\[PAGE\s+\d+\]\]", " ", body)
        body = clean_text(body)
        pages = extract_source_pages(segment, start_page)

        record = {
            "standard_id": standard_id,
            "title": title,
            "scope": scope,
            "pages": pages,
            "text": body[:7000],
        }

        if standard_id in records:
            existing = records[standard_id]
            existing["text"] = clean_text(str(existing["text"]) + " " + body)[:9000]
            existing["pages"] = sorted(set(existing.get("pages", []) + pages))[:10]
            if not existing.get("scope") and scope:
                existing["scope"] = scope
            if not existing.get("title") and title:
                existing["title"] = title
        else:
            records[standard_id] = record

    return list(records.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BIS SP 21 standards index")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    standards = parse_standards(args.pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "source": str(args.pdf.as_posix()),
                "standard_count": len(standards),
                "standards": standards,
            },
            file,
            ensure_ascii=True,
            indent=2,
        )

    print(f"Wrote {len(standards)} standards to {args.output}")


if __name__ == "__main__":
    main()
