"""Judge entrypoint for the BIS Standards Recommendation Engine.

Required command:
python inference.py --input hidden_private_dataset.json --output team_results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.retriever import load_retriever


def run(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as file:
        queries = json.load(file)

    retriever = load_retriever()
    output = []

    for item in queries:
        results, latency = retriever.recommend(str(item.get("query", "")), top_k=5)
        row = {
            "id": item.get("id"),
            "retrieved_standards": [result["standard_id"] for result in results],
            "latency_seconds": round(latency, 4),
        }

        # Keeping expected_standards when present makes local eval_script.py usable
        # on the public test set. Hidden judging can ignore this extra field.
        if "expected_standards" in item:
            row["expected_standards"] = item["expected_standards"]

        output.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BIS standards recommendations")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()

