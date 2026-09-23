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
│
├── evaluation/
│   ├── test_dataset.json        # queries mapped to expected cases
│   ├── evaluate.py              # accuracy + latency measurement
│   └── results.json             # results output by evaluate.py
│
├── services/
│   ├── filtering_service.py     # metadata filtering (Day 3)
│   ├── ranking_service.py       # combined score ranking (Day 4)
│   └── multimodal_service.py    # image + text embedding fusion (Day 5)
│
├── generate_embeddings.py       # case image -> 512-D embeddings
├── create_metadata.py           # realistic case metadata (30-50 cases)
├── build_faiss_index.py         # build/save index from embeddings
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

```bash
# 1. Build the dataset and metadata
python create_metadata.py

# 2. Generate embeddings for every case image
python generate_embeddings.py

# 3. Build the FAISS index
python build_faiss_index.py

# 4. Run the standalone search experiment
python similarity_search.py

# 5. Evaluate accuracy and latency
python evaluation/evaluate.py

# 6. Start the integrated API
python app.py            # http://localhost:8000, docs at /docs
```

## 9. Week 03 Deliverables Checklist

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | Realistic 30-50 case dataset (`data/persons`, `data/pets`, `data/items`) |  |
| 2 | Metadata filtering (`services/filtering_service.py`) |  |
| 3 | Image + text multimodal search (`services/multimodal_service.py`) |  |
| 4 | Ranking system (`services/ranking_service.py`) |  |
| 5 | Combined similarity score (visual + text + location) |  |
| 6 | Accuracy evaluation (`evaluation/evaluate.py`, `results.json`) |  |
| 7 | Fully integrated FastAPI API (`app.py`) |  |

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