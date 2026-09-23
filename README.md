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

## Week 03: Measure Before Improving

The first Week 03 milestone is a small evaluation layer. It is intentionally independent of PyTorch, Transformers, FAISS, and the running services, so it can be learned and tested quickly:

```bash
cd learning/Week-03
python -m unittest discover -s tests -v
```

The evaluator supports reciprocal rank and recall at `k`. It consumes a query's ranked case IDs and its expected matching case IDs, which makes it possible to compare retrieval changes using a fixed evaluation set.

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
4. Use the Week 03 evaluator to establish a baseline.
5. Change one variable at a time: labels, data, weights, or retrieval code.
6. Record the metric change and the reason for the next experiment.

The project is a learning assistant for the FYP journey when every experiment leaves behind both code and an explanation of what was learned.
