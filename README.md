# Lostify AI

Lostify AI is an educational lost-and-found search system built in small, testable milestones. It uses CLIP to place images and text in a shared embedding space, then ranks known cases with cosine similarity or a FAISS inner-product index.

## Current Architecture

```text
React frontend
	-> Node.js API (reports, uploads, orchestration)
		-> FastAPI AI service (CLIP embeddings and FAISS search)
			-> case embeddings + metadata
```

The project deliberately keeps the learning stages visible:

- `learning/Week-01/` contains the first direct image-similarity experiment.
- `learning/Week-02/` separates embedding generation from retrieval and adds the API, frontend, and report registry.
- `learning/Week-03/` measures retrieval quality before model or dataset changes are introduced.
- `documentation/` contains the weekly plan and project decisions.

## Week 03: Complete Matching Engine

Week 03 turns the Week 02 CLIP + FAISS pipeline into an accurate, explainable
matching engine with a 44-case dataset (14 pets / 10 persons / 20 items):
metadata filtering, a weighted visual + text + location ranking, true
multimodal image+text search, an integrated FastAPI service, and a measured
evaluation baseline.

```text
Overall   n=47  Top-1 93.6%  Top-5 97.9%  Top-10 100%  MRR 0.9605
Text      n=29  Top-1 89.7%   (the honest, harder mode)
Combined  n=6   Top-1 100%
FAISS search  0.004 ms  |  Total search ~80-110 ms (CLIP on CPU)
```

A complete **React + Tailwind frontend** (`learning/Week-03/frontend/`) is wired
to the API: report a loss (photo + text + type + city) → top 5 matches with
explainable score bars on `/`, and all 44 dataset cases as a filterable gallery
on `/reports`. CORS + image serving (`/static`) are enabled on the FastAPI side.

```bash
cd learning/Week-03
python app.py          # terminal 1 — API on :8000
cd frontend
npm install
npm run dev            # terminal 2 — UI on :5173
```

Unit tests are fast and dependency-free (no model load):

```bash
cd learning/Week-03
python -m unittest discover -s tests -v
```

The evaluator (`evaluation/evaluate.py`) supports reciprocal rank and
recall/top-k accuracy, and writes `evaluation/results.json`. See
`learning/Week-03/README.md` for the full run order, the results, and the
candidate next experiments.

## Running Week 02

Run the Python AI service from `learning/Week-02` after installing its dependencies:

```bash
cd learning/Week-02
python create_metadata.py
python generate_embeddings.py
python build_faiss_index.py
uvicorn app:app --reload --port 8000
```

In another terminal, run the Node.js API:

```bash
cd learning/Week-02/backend
npm install
npm start
```

The frontend can then be started with:

```bash
cd learning/Week-02/frontend
npm install
npm run dev
```

The first CLIP run downloads model files and requires a working Python environment with `torch`, `transformers`, `Pillow`, `numpy`, `faiss-cpu`, and `fastapi` installed. The Week 03 tests do not require those packages.

## Learning Order

1. Explain the Week 01 embedding and cosine-similarity experiment.
2. Explain why Week 02 precomputes case embeddings.
3. Trace a request through React, Node.js, FastAPI, CLIP, and FAISS.
4. Use the Week 03 evaluator baseline (`learning/Week-03/evaluation/results.json`).
5. Change one variable at a time: labels, data, weights, or retrieval code.
6. Record the metric change and the reason for the next experiment.

The project is a learning assistant for the FYP journey when every experiment leaves behind both code and an explanation of what was learned.
