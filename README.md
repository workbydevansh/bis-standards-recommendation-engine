# BIS Standards Recommendation Engine

Submission-ready prototype for the Bureau of Indian Standards x Sigma Squad AI Hackathon.

The system converts a product description into the top 3-5 relevant BIS standards from **SP 21: Summaries of Indian Standards for Building Materials**. It is deterministic, offline, and designed around the required judging contract.

## Judge Command

```bash
python inference.py --input hidden_private_dataset.json --output team_results.json
```

The output JSON contains:

- `id`
- `retrieved_standards`
- `latency_seconds`

When the input contains `expected_standards`, the field is copied into the output so the provided `eval_script.py` can be run locally.

## Quick Start

```bash
python -m pip install -r requirements.txt
python src/build_index.py
python inference.py --input data/public/public_test_set.json --output data/public/team_results.json
python eval_script.py --results data/public/team_results.json
```

## Local Demo

The demo UI is a React app served by the Python backend.

```bash
cd frontend
npm install
npm run build
cd ..
python app.py
```

Open `http://127.0.0.1:8000` and enter a product description.

For frontend-only development, run the Python backend in one terminal and Vite in another:

```bash
python app.py
cd frontend
npm run dev
```

## Architecture

```text
data/raw/dataset.pdf
        |
        v
src/build_index.py
        |
        v
data/index/standards.json
        |
        v
src/retriever.py  ->  inference.py / app.py / frontend
```

## Retrieval Strategy

The retriever combines:

- BM25-style lexical scoring over standard IDs, titles, scopes, and summaries.
- Field boosts for exact standard IDs, standard numbers, product phrases, grade numbers, and title coverage.
- Deterministic reranking that only returns standard IDs parsed from the official PDF index.

This avoids hallucinated standards and keeps latency well below the 5 second target on normal hardware.

## Repository Structure

```text
src/
  build_index.py
  retriever.py
data/
  raw/dataset.pdf
  index/standards.json
  public/public_test_set.json
  public/sample_output.json
  public/team_results.json
inference.py
eval_script.py
app.py
frontend/
  src/
  dist/
  package.json
  package-lock.json
requirements.txt
presentation.pdf
```

## Dataset

The official dataset is the BIS SP 21 PDF provided by the organizers:

`data/raw/dataset.pdf`

The generated searchable index is:

`data/index/standards.json`
