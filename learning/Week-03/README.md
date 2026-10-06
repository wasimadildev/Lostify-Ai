# Lostify AI - Week 03
## AI Matching Engine and Case Retrieval

### Week Objective

Week 03 takes the Week 02 pipeline (CLIP + FAISS + FastAPI) and turns it into an accurate, explainable, and usable matching engine.

Week 02 finds visually similar cases. Week 03 needs to find the *right* case. That means filtering out wrong categories, ranking with a meaningful combined score, supporting image + text queries together, and measuring accuracy with real numbers.

```text
User Report
    |
    v
Image/Text -> CLIP Embedding
    |
    v
FAISS Search -> Candidate Cases (Top 20)
    |
    v
Metadata Filtering (category / location / date)
    |
    v
Filtering/Reranking -> Match Score
    |
    v
API Response -> Frontend
```

### The Problem We Are Solving in Week 03

The Week 02 system has one weakness: a pure visual FAISS search does not understand *what kind* of thing the user lost.

For a query like "Lost white cat", FAISS can return:

```text
White dog    <- visually similar, wrong type
White shirt  <- color matches, wrong type
White car    <- color matches, wrong type
White cat    <- correct
```

That is not acceptable for an FYP demo. Week 03 fixes this with metadata filtering, a weighted ranking score, and proper multimodal queries.

## 1. Where We Are Right Now (Start of Week 03)

The Week 02 pipeline is the starting point. It already does the first half of the final Week 03 goal:

```text
User Report
    |
    v
Image/Text -> CLIP Embedding -> FAISS Search -> Candidate Cases
```

### 1.1 `generate_embeddings.py`

Creates and saves case embeddings.

- Loads `openai/clip-vit-base-patch32`.
- For each case image: opens it, converts to RGB, runs it through the CLIP vision model, projects to 512 dimensions, normalizes, and saves as `.npy` in `embeddings/`.
- Runs once per case image, not once per search.

### 1.2 `create_metadata.py`

Creates `metadata.json` for the case images.

Current metadata is image-grounded and includes: image path, title, category (Luggage, Bag, Bicycle, Electronics, etc.), location (mostly `Unknown` right now), description, and notes.

Missing for Week 03: `case_id`, `case_type` (lost_pet / lost_item / lost_person), category as a controlled set, latitude/longitude, `date_lost`, and `status`.

### 1.3 `build_faiss_index.py`

Loads the saved `.npy` embeddings, normalizes each vector with `faiss.normalize_L2`, builds an `IndexFlatIP` (inner product on normalized vectors = cosine similarity), and writes:

- `embeddings.index`
- `embeddings_case_names.txt` (keeps the case order)

### 1.4 `similarity_search.py`

The search experiment script.

- Loads the CLIP model (for the query only).
- Loads all saved case embeddings.
- Supports image-only, text-only, and combined search by scoring separately and summing with weights.
- Later versions use the FAISS index and search the full index (`index.search(query_emb, index.ntotal)`) so image and text scores can be combined per case.

### 1.5 `app.py` (FastAPI)

The search API.

- Loads CLIP and the FAISS index once at startup (no per-case inference at request time).
- `POST /search` accepts `image` (UploadFile), `text`, `weight_image`, `weight_text`, `top_k`.
- Auto-adjusts weights when only one modality is provided.
- Returns the top-k cases with metadata (title, category, location, description) and a single `similarity_score`.

### 1.6 Embedding dimensions and normalization (verified)

- Model: `openai/clip-vit-base-patch32`
- Image embeddings: 512-dimensional, `visual_projection` output, L2-normalized.
- Text embeddings: 512-dimensional, `text_projection` output, L2-normalized.
- FAISS index: `IndexFlatIP(512)`, vectors normalized with `faiss.normalize_L2` before `add`.
- Everything is in the same 512-D shared CLIP space, so image and text vectors are directly comparable.

### 1.7 What Week 02 already gives us

- Image -> embedding -> search (works)
- Text  -> embedding -> search (works)
- Image + Text -> weighted combined search (works at a basic level)

## 2. The Missing Pieces (What Week 03 Builds)

| Capability | Week 02 | Week 03 |
| --- | --- | --- |
| Realistic dataset | 10 generic item images | 30-50 real cases across `pets/`, `persons/`, `items/` |
| Rich metadata | title, category, location | case_id, case_type, category, description, lat/lon, date_lost, status |
| FAISS candidate pool | direct top-k | Top 20 candidates, then filter |
| Type awareness | none | metadata filtering (pets vs items vs persons) |
| Ranking | single similarity score | combined score (visual + text + location) |
| Explainability | one number | visual_score, text_score, location_score, final_score |
| Multimodal query | crude weight sum of scores | true combined embedding, then one FAISS search |
| Evaluation | none | accuracy metrics (Top-1 / Top-5 / Top-10) and latency |
| API | search only | full integrated search with filtering + ranking |

## 3. Week 03 Architecture (Target)

```text
                       Lostify AI
                           |
                           v
                     User Search
                           |
              +------------+------------+
              |                         |
           Image                      Text
              |                         |
              v                         v
           CLIP                        CLIP
              |                         |
              v                         v
      Image Embedding           Text Embedding
              |                         |
              +------------+------------+
                           |
                           v
                  Combined Embedding
                           |
                           v
                        FAISS
                           |
                     Top 20 Results
                           |
                           v
                  Metadata Filtering
                          (type / category / location / date)
                           |
                           v
                     Ranking Engine
                    (visual + text + location)
                           |
                           v
                    Final Score (0-1)
                           |
                           v
                      Top 5 Matches
                           |
                           v
                       FastAPI
                           |
                           v
                       Frontend
```

## 4. Week 03 Plan (Day by Day)

### Day 1 - Understand and Improve the Current Pipeline

Review `generate_embeddings.py`, `similarity_search.py`, `build_faiss_index.py`, and `app.py`, then verify end to end:

- Confirm embedding dimensions (512).
- Confirm normalization.
- Test FAISS search manually.
- Test image -> image matching.
- Test text -> image matching.

Practical test setup:

```text
5-10 lost-item images
5-10 lost-pet images
5-10 person images
```

Run:

```text
Query Image
    |
    v
   CLIP
    |
    v
Embedding
    |
    v
  FAISS
    |
    v
Top 5 Cases
```

Deliverable: this README, documenting the current pipeline.

### Day 2 - Improve Dataset and Metadata

Create a proper case structure:

```json
{
  "case_id": "CASE-001",
  "case_type": "lost_pet",
  "category": "cat",
  "description": "White Persian cat with blue collar",
  "location": "Islamabad",
  "latitude": 33.6938,
  "longitude": 73.0652,
  "date_lost": "2026-09-01",
  "image_path": "data/pets/case_001.jpg",
  "status": "open"
}
```

- Improve `create_metadata.py` to generate this schema.
- Create 30-50 realistic test cases.
- Organize images by category:

```text
data/
├── persons/
├── pets/
└── items/
```

- Add a controlled set of categories (cat, dog, bag, phone, bicycle, person, etc.).

Deliverable: a realistic Lostify AI test dataset.

### Day 3 - Build Intelligent Filtering

Problem: FAISS returns visually similar but wrong-type results. Solution: metadata filtering on the FAISS candidates.

```text
Query
  |
  v
CLIP
  |
  v
FAISS Top 20
  |
  v
Metadata Filtering (case_type, category, location, date)
  |
  v
Top 5
```

```python
if query_type == "lost_pet":
    results = [
        r for r in results
        if r["case_type"] == "lost_pet"
    ]
```

Deliverable: `services/filtering_service.py`.

### Day 4 - Similarity Score and Ranking

Replace the single CLIP similarity with a weighted, explainable score:

```text
Final Score = 0.70 * Visual Similarity
            + 0.20 * Text Similarity
            + 0.10 * Location Relevance
```

Example:

```text
Visual similarity: 0.89
Text similarity:   0.82
Location score:    0.90

Final Score = 0.70(0.89) + 0.20(0.82) + 0.10(0.90) = 0.875
```

Response shape:

```json
{
  "case_id": "CASE-023",
  "visual_score": 0.89,
  "text_score": 0.82,
  "location_score": 0.90,
  "final_score": 0.875
}
```

Deliverable: `services/ranking_service.py`.

### Day 5 - Improve Multimodal Search

Week 02 supports image -> and text -> search separately. Week 03 makes image + text -> search a true combined embedding.

```text
Query: cat picture  +  "White Persian cat wearing a blue collar lost in Islamabad."

              +-- Image --> CLIP --> Image Embedding --+
User Query ---+                                        +--> Combined Search
              +-- Text  --> CLIP --> Text Embedding  --+
```

```python
combined = 0.7 * image_embedding + 0.3 * text_embedding
combined = combined / np.linalg.norm(combined)   # normalize
```

Then one FAISS search on the combined vector.

Deliverable: `services/multimodal_service.py` and an API that supports `POST /search` with `image` and/or `text`.

### Day 6 - Evaluation and Accuracy Testing

Turn "the AI works" into measurable results.

- Create an evaluation dataset: ~50 queries, each mapped to its expected case.
- Measure for each query whether the correct case appeared at rank 1, in the top 5, and in the top 10.
- Also measure search latency.

```text
Total Queries: 50
Top-1 Accuracy: 72%
Top-5 Accuracy: 88%
Top-10 Accuracy: 94%

FAISS search:        12 ms
Total API response: 180 ms
```

Deliverable:

```text
evaluation/
├── test_dataset.json
├── evaluate.py
└── results.json
```

### Day 7 - Integrate Everything

Combine filtering, ranking, and multimodal search into one FastAPI pipeline and test the full flow from request to frontend.

Deliverable: fully integrated API.

## 5. Week 03 Folder Structure

```text
learning/Week-03/
│
├── README.md                    # this document
│
├── data/
│   ├── persons/                 # lost-person images
│   ├── pets/                    # lost-pet images
│   └── items/                   # lost-item images
│
├── embeddings/                  # generated .npy vectors + FAISS index
│   ├── *.npy                    # one 512-D vector per case
│   ├── index.index              # FAISS IndexFlatIP (44 vectors)
│   └── case_names.txt           # case order matching the index
│
├── evaluation/
│   ├── test_dataset.json        # 47 queries mapped to expected cases
│   ├── metrics.py               # dependency-free metrics
│   ├── evaluate.py              # accuracy + latency runner
│   └── results.json             # results output by evaluate.py
│
├── services/
│   ├── __init__.py
│   ├── store.py                 # CaseStore: metadata + FAISS index wrapper
│   ├── filtering_service.py     # metadata filtering (Day 3)
│   ├── ranking_service.py       # combined score ranking (Day 4)
│   └── multimodal_service.py    # image + text embedding fusion (Day 5)
│
├── tests/                       # unit tests (no model loads, fast)
│   ├── test_metrics.py
│   ├── test_services.py
│   └── test_db.py                # sqlite + index persistence tests
│
├── db.py                        # SQLite layer (lostify.db) + seeding
├── lostify.db                   # SQLite database (44 seeded + new reports)
├── catalog.json                 # single source of truth (44 cases)
├── metadata.json                # generated rich metadata
├── requirements.txt             # pinned Python dependencies
│
├── frontend/                    # React + Tailwind (Vite) UI
│   ├── index.html
│   ├── vite.config.js           # react + tailwindcss vite plugins
│   └── src/
│       ├── main.jsx             # React entry
│       ├── App.jsx              # router + layout (/, /new-report, /reports)
│       ├── api.js               # fetch helpers for /search, /cases, /reports, /health
│       ├── index.css            # tailwindcss import
│       ├── components/          # Header, Footer, Dropzone, ResultCard,
│       │                        # CaseCard, ScoreBars, StatusBadge
│       └── pages/               # SearchPage (report form + top 5),
│                                # NewReportPage (database submission),
│                                # ReportsPage (all-reports gallery)
│
├── download_dataset.py          # fetch web images (Openverse + Wikipedia fallback)
├── verify_dataset.py            # CLIP zero-shot probe + --fix Wikipedia fallback
├── create_metadata.py           # realistic case metadata (44 cases)
├── generate_embeddings.py       # case image -> 512-D embeddings
├── build_faiss_index.py         # build/save index from embeddings
├── engine.py                    # CLIPEngine: search pipeline shared by all entry points
├── similarity_search.py         # standalone search experiment script
└── app.py                       # integrated FastAPI search service
```

## 6. Key Design Decisions for Week 03

### 6.1 Combined embedding, not combined scores

Week 02 searched FAISS twice (once per modality) and added the two score vectors. Week 03 should compute one weighted, normalized embedding and search FAISS once:

```python
combined = 0.7 * image_embedding + 0.3 * text_embedding
combined = combined / np.linalg.norm(combined)
indices, scores = index.search(combined.reshape(1, -1), 20)
```

One search call, and the candidate set naturally reflects both modalities.

### 6.2 FAISS returns candidates, filtering decides

Ask FAISS for a wide net (top 20). Then filter by `case_type`, `category`, location, and date. Filtering first, ranking second.

### 6.3 Explainable scores

Keep `visual_score`, `text_score`, and `location_score` separate in the response so a user (and an examiner) can see *why* a case matched. The `final_score` is the weighted combination.

### 6.4 Normalization everywhere

Keep embeddings unit-normalized at every stage (generation, fusion, query). This keeps inner-product = cosine similarity consistent through the whole pipeline.

### 6.5 Evaluation can be simple

Top-1 / Top-5 / Top-10 accuracy and average latency is enough for an honest FYP metric. No need for precision/recall curves this week.

## 7. Expected API

```http
POST /search
```

Form fields:

| Field | Type | Notes |
| --- | --- | --- |
| `image` | file (optional) | uploaded lost item/pet/person image |
| `text` | string (optional) | description of the lost item |
| `query_type` | string (optional) | `lost_pet`, `lost_item`, `lost_person`; used for filtering |
| `location` | string (optional) | city/area, used for location score |
| `top_k` | int (optional, default 5) | number of results |

At least one of `image` or `text` is required.

### Adding new reports (Persistence layer)

`GET /reports` lists every report (dataset seed + user submissions) and
`POST /reports` saves a brand-new lost report:

| Field | Type | Notes |
| --- | --- | --- |
| `image` | file (required) | photo of the lost pet / item / person |
| `title` | string (optional) | short display title |
| `description` | string (optional) | details embedded by CLIP for search |
| `case_type` | string | `lost_pet`, `lost_item`, `lost_person` |
| `category` | string (optional) | cat, dog, bicycle, … |
| `location` | string (optional) | city/area |
| `latitude` / `longitude` | float (optional) | for the location score |
| `date_lost` | string (optional) | date |

`POST /reports` flow:

```text
multipart upload -> save JPEG to data/<type>/<id>.jpg
                 -> CLIP-embed -> CaseStore.add_case() -> FAISS index + metadata files
                 -> INSERT INTO lostify.db (source = 'user')
```

- New IDs continue the dataset prefixes (`PERS-11`, `PETS-15`, `ITEMS-21`).
- The case is embeddable **and** searchable immediately — no server restart.
- `source` marks `'dataset'` (seeded) vs `'user'` entries; the frontend tags
  user submissions with a "New report" badge.

Example response item:

```json
{
  "case_id": "CASE-023",
  "case_type": "lost_pet",
  "category": "cat",
  "title": "White Persian Cat with Blue Collar",
  "location": "Islamabad",
  "visual_score": 0.89,
  "text_score": 0.82,
  "location_score": 0.90,
  "final_score": 0.875
}
```

## 8. How to Run (Week 03 Order)

All scripts run from `learning/Week-03` (Python 3.13, deps in `requirements.txt`).
Any script that imports both `faiss` and `torch` on macOS needs the OpenMP workaround:

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
```

```bash
# 0. Install dependencies once
python -m pip install -r requirements.txt

# 1. Build the case catalog (source of truth for metadata)
python create_metadata.py

# 2. Verify images / optionally fix mismatches (uses Wikipedia fallback)
python verify_dataset.py            # add --fix to replace broken cases

# 3. Generate embeddings for every case image
python generate_embeddings.py

# 4. Build the FAISS index
python build_faiss_index.py

# 5. Run the standalone search experiment
python similarity_search.py --text "lost golden retriever dog in Karachi" --query_type lost_pet

# 6. Run the unit tests (no model load, no GPU)
python -m unittest discover -s tests -v

# 7. Evaluate accuracy and latency
python evaluation/evaluate.py       # writes evaluation/results.json

# 8. Start the integrated API
python app.py                       # http://localhost:8000, docs at /docs

# 9. Start the React + Tailwind frontend (in a second terminal)
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

The frontend has three pages that consume the API directly:

- **`/` — Search**: upload a photo and/or description + type + city →
  `POST /search` → shows the **top 5 matches** with explainable
  visual/text/location/final score bars.
- **`/new-report` — New report**: upload a photo + details →
  `POST /reports` → saved to the **SQLite database** and added to the FAISS
  index, with a success panel linking to the gallery or straight into a search.
- **`/reports` — All reports**: `GET /reports` → a grid gallery of every
  report (44 seeded + new submissions) with type + status badges and a
  "New report" tag for user-submitted cases.

CORS is enabled on the API and case images are served from
`http://localhost:8000/static/…` so the browser can render thumbnails.

Notes:

- `download_dataset.py` is only needed to fetch fresh web images; the 44 case
  images already live in `data/`.
- The evaluation set is generation-anchored: image queries reuse a case image,
  so image-mode accuracy is expected to be near 100%. Text queries measure the
  harder, realistic part.

## 9. Week 03 Deliverables Checklist

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | Realistic 30-50 case dataset (`data/persons`, `data/pets`, `data/items`) | ✅ 44 cases (14 pets / 10 persons / 20 items), `catalog.json` + `metadata.json` |
| 2 | Metadata filtering (`services/filtering_service.py`) | ✅ tested (`tests/test_services.py`) |
| 3 | Image + text multimodal search (`services/multimodal_service.py`) | ✅ true combined embedding |
| 4 | Ranking system (`services/ranking_service.py`) | ✅ visual 0.70 / text 0.20 / location 0.10 |
| 5 | Combined similarity score (visual + text + location) | ✅ `final_score` with explainable parts |
| 6 | Accuracy evaluation (`evaluation/evaluate.py`, `results.json`) | ✅ 47 queries, results in `results.json` |
| 7 | Fully integrated FastAPI API (`app.py`) | ✅ `POST /search` smoke-tested end to end |
| 8 | React + Tailwind frontend (report → top 5 matches → gallery) | ✅ `frontend/`, wired to `/search` + `/reports`, image serving + CORS on the API |
| 9 | Database persistence (`db.py`, `lostify.db`) | ✅ SQLite, seeded from `metadata.json`, `source` column |
| 10 | New lost-report flow (save → embed → searchable) | ✅ `POST /reports` + `CaseStore.add_case()` + `/new-report` page, 41/41 tests |

## 10. Week 03 Outcome (Definition of Done)

At the end of Week 03, Lostify AI has:

```text
CLIP -> FAISS -> Filtering -> Ranking -> Evaluation -> API
```

- A realistic 30-50 case dataset organized by type.
- A search that does not return a white dog for a lost white cat.
- A search that accepts an image, text, or both at once.
- An explainable final score per match.
- Measured Top-1 / Top-5 / Top-10 accuracy and latency.
- One integrated FastAPI endpoint servicing the frontend.

Do not move to YOLO, ArcFace, OCR, or other models until this solid pipeline is complete.

## 11. Week 03 Results (Measured Baseline)

Produced by `evaluation/evaluate.py` on `evaluation/results.json`
(44-case FAISS index, `openai/clip-vit-base-patch32`, CPU).

```text
Overall   n=47  Top-1 93.6%  Top-5 97.9%  Top-10 100%  MRR 0.9605
Image     n=12  Top-1 100%      MRR 1.0000
Text      n=29  Top-1 89.7%     MRR 0.9360   (image anchoring absent)
Combined  n=6   Top-1 100%      MRR 1.0000

By case type:
Lost pets    n=19  Top-1 100%
Lost persons n=10  Top-1 90.0%  (weakest: text-only toddler description GAP)
Lost items   n=18  Top-1 88.9%  (weakest: visually generic objects)

Latency:
FAISS search    0.004 ms (avg)
Total search    ~80-110 ms (avg, includes CLIP inference)
```

Known gaps:

- Text mode is the honest measurement: two queries miss Top-1 (PERS-07 toddler
  described by clothing, ITEMS-18 generic water bottle). Both improve when the
  user also supplies an image (combined mode is 100%).

## 12. Next Experiments (Week 04 Candidates)

Change exactly one variable at a time and record the metric delta against the
baseline above:

1. Ranking weights (visual/text/location), e.g. text 0.30 for text-only queries.
2. Candidate pool size (`candidate_k` 20 -> 50) for harder recall cases.
3. Dataset: add images of the same objects in different backgrounds.
4. Text pre-processing (title + description vs description only).
5. `IndexFlatIP` -> `IndexIVFFlat` and measure latency vs recall trade-off.