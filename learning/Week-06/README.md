# Lostify AI - Week 06
## Production AI Service: FastAPI + PostgreSQL/PostGIS + FAISS + Model Serving + Docker + Async Processing + API Integration

### Week Objective

Week 06 is the transition from **AI experiments** to a **real backend AI service**.

By the end of the week, a lost report sent from the application flows end to end:

```text
Flutter / React
       │
       │ HTTP
       ▼
Node.js Backend
       │
       │ REST
       ▼
Python AI Service
       │
       ├── YOLO
       ├── CLIP
       ├── OCR
       ├── Face Recognition
       ├── FAISS
       └── PostgreSQL/PostGIS
              │
              ▼
        Matching Results
```

### Key Principle

> Don't put all AI logic inside the Node.js backend. Keep AI inference in a dedicated Python service.

Node.js handles product logic; Python handles AI. Never mix the two.

## 1. Week 06 Goals

- [ ] Production-style FastAPI service
- [ ] PostgreSQL database
- [ ] PostGIS location support
- [ ] FAISS vector search
- [ ] CLIP model loaded once
- [ ] YOLO model loaded once
- [ ] OCR service integrated
- [ ] Face service integrated where appropriate
- [ ] Image upload pipeline
- [ ] Async/background processing
- [ ] Search API
- [ ] Case creation API
- [ ] Match API
- [ ] Dockerized AI service
- [ ] Docker Compose local environment
- [ ] Health checks
- [ ] Logging
- [ ] Error handling
- [ ] Node.js → Python AI integration
- [ ] Flutter → Node.js → AI integration
- [ ] API documentation

## 2. Final Week 06 Architecture

```text
                         LOSTIFY AI
                             │
              ┌──────────────┴──────────────┐
              │                             │
           Flutter                       React
          Mobile App                    Web Portal
              │                             │
              └──────────────┬──────────────┘
                             │
                             ▼
                    Node.js / Express
                       Main Backend
                             │
            ┌────────────────┼─────────────────┐
            │                │                 │
            ▼                ▼                 ▼
       PostgreSQL         Firebase         AI Service
        + PostGIS        Notifications       │
                                               │
                                      ┌────────┼─────────┐
                                      │        │         │
                                     CLIP     YOLO      OCR
                                      │        │         │
                                      └────────┼─────────┘
                                               │
                                               ▼
                                          FAISS Index
                                               │
                                               ▼
                                         PostgreSQL
```

## 3. Week 06 Repository Structure

```text
learning/Week-06/
│
├── README.md
│
├── ai-service/
│   ├── app/
│   │   ├── main.py                 # FastAPI app: routers + startup
│   │   ├── api/
│   │   │   ├── health.py           # GET /health
│   │   │   ├── cases.py            # POST /cases, GET /cases/{id}
│   │   │   ├── search.py           # POST /search
│   │   │   └── matches.py          # find-matches + get matches
│   │   ├── core/
│   │   │   ├── config.py           # env-driven configuration
│   │   │   ├── logging.py          # structured request/case/job logs
│   │   │   └── security.py         # auth between services, validation
│   │   ├── models/
│   │   │   ├── request.py          # Pydantic request models
│   │   │   └── response.py         # Pydantic response models
│   │   ├── services/
│   │   │   ├── clip_service.py
│   │   │   ├── yolo_service.py
│   │   │   ├── ocr_service.py
│   │   │   ├── face_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── faiss_service.py
│   │   │   ├── matching_service.py
│   │   │   └── storage_service.py
│   │   ├── database/
│   │   │   ├── connection.py       # SQLAlchemy / async engine
│   │   │   ├── models.py           # SQLAlchemy ORM models
│   │   │   └── repository.py       # data access layer
│   │   └── workers/
│   │       └── tasks.py            # background AI processing
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── database/
│   ├── init.sql                    # schema + PostGIS enable
│   └── seed.sql                    # sample cases
│
├── docker/
│   └── docker-compose.yml
│
├── tests/
│   ├── test_health.py
│   ├── test_search.py
│   ├── test_matching.py
│   └── test_database.py
│
└── docs/
    ├── architecture.md
    └── api.md
```

## 4. Responsibility Split

| Layer | Responsibilities |
| --- | --- |
| **Node.js** | Authentication, users, reports, cases, permissions, notifications, business logic, API gateway |
| **Python AI Service** | CLIP, YOLO, OCR, Face, embeddings, FAISS, AI matching, model inference |
| **PostgreSQL / PostGIS** | Users, cases, reports, locations, metadata, matches, jobs |
| **FAISS** | Fast vector retrieval only |
| **Flutter** | Mobile UI, camera, image upload, maps, notifications, user interaction |
| **React** | Admin / NGO / police portal, case management, analytics |

## 5. Week 06 Plan (Day by Day)

### Day 1 — Production FastAPI Foundation

Turn the Week 05 AI pipeline into a proper FastAPI application.

```text
FastAPI
   │
   ├── /health
   ├── /cases
   ├── /search
   └── /matches
```

#### Application structure

```text
main.py
    ↓
routers
    ↓
services
    ↓
repositories
```

Do NOT put everything in `main.py`:

```text
AVOID:
main.py
  ├── CLIP
  ├── YOLO
  ├── FAISS
  ├── SQL
  ├── image processing
  └── matching
```

#### Health endpoint

```http
GET /health
```

```json
{
  "status": "healthy",
  "service": "lostify-ai",
  "version": "1.0.0"
}
```

Extended later:

```json
{
  "status": "healthy",
  "models": { "clip": true, "yolo": true, "ocr": true, "face": true },
  "faiss": true,
  "database": true
}
```

#### Configuration (`core/config.py`)

Use environment variables, never hard-code:

```text
DATABASE_URL
FAISS_INDEX_PATH
MODEL_PATH
UPLOAD_DIR
MAX_IMAGE_SIZE
NODE_BACKEND_URL
```

Never hard-code:

```text
database password
API keys
secret keys
production URLs
```

### Day 2 — PostgreSQL + PostGIS

Move case data from JSON files into PostgreSQL.

#### Case table

```text
cases
────────────────────────
id
case_id
user_id
case_type
category
title
description
status
image_url
created_at
updated_at
```

Lostify also needs location. Prefer a PostGIS `geography/geometry` column over raw `latitude`/`longitude` values.

```json
{
  "case_id": "CASE-0001",
  "type": "lost_pet",
  "category": "cat",
  "title": "Lost Persian Cat",
  "description": "White Persian cat with blue collar",
  "latitude": 33.6844,
  "longitude": 73.0479
}
```

#### Why PostGIS?

A lost case in Islamabad and a found case in Rawalpindi can be compared with real distance. Location becomes a ranking signal:

```text
Visual similarity:    0.91
Location relevance:   0.82
```

Spatial queries:

```text
Find cases within 10 km
```

```text
PostGIS
    ↓
Spatial query
    ↓
Candidate cases
```

### Day 3 — FAISS Production Integration

Turn the Week 02 prototype (`generate_embeddings.py` → `.npy` → `build_faiss_index.py`) into a service.

Create `services/faiss_service.py` with:

```text
load_index()
add_embedding()
search()
remove_embedding()
save_index()
reload_index()
```

#### Load once, keep in memory

```text
BAD:
Request → Load 5000 embeddings → Build FAISS → Search → Response

GOOD:
Application startup → Load FAISS → Keep in memory
Request → Search
```

#### FAISS is not the source of truth

```text
PostgreSQL  → source of truth
FAISS       → fast vector retrieval
```

```text
FAISS result: case_id = CASE-104
    ↓
PostgreSQL: full case information
```

### Day 4 — Model Serving

One of the most important days. Load models **once at startup**, not per request.

```text
BAD:
POST /search → load CLIP, YOLO, OCR, Face → infer → respond

GOOD:
FastAPI Startup → Load CLIP, YOLO, OCR, Face, FAISS
Request → Existing models → Inference
```

#### Model manager

Create `services/model_manager.py`:

```text
ModelManager
   │
   ├── clip_model
   ├── yolo_model
   ├── ocr_model
   └── face_model
```

#### Device detection

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
```

This makes the service portable between CPU dev machines and GPU servers.

### Day 5 — Image Processing + Async Processing

Images can be large (10 MB) and the full pipeline (YOLO + OCR + Face + CLIP + FAISS + Ranking) can be slow. Do not block the request on heavy inference.

#### Async vs background processing

`async def` alone does **not** make CPU/GPU-heavy ML inference asynchronous. Use a background worker for inference.

```text
Fast operation (synchronous):
POST /cases → Validate → Store image → Create case
             → Return job/case ID

Background worker (later):
YOLO → OCR → Face → CLIP → FAISS → Matching
```

#### Job status

```text
processing_jobs
```

States:

```text
queued
processing
completed
failed
```

```http
GET /jobs/{job_id}
```

```json
{
  "job_id": "JOB-001",
  "status": "processing",
  "progress": 65
}
```

Start with FastAPI `BackgroundTasks`/a simple worker. Move to Celery/RQ + Redis only when inference gets heavy or multiple workers are needed. Understand the architecture before adding infrastructure.

### Day 6 — Build the Matching API

Expose the AI system through APIs.

#### API 1 — Create case

```http
POST /cases
```

Input: `image, title, description, case_type, category, latitude, longitude`

```text
POST /cases
      ↓
Validate
      ↓
Store case
      ↓
Store image
      ↓
Create job
      ↓
Return case_id + job_id
```

```json
{ "case_id": "CASE-104", "job_id": "JOB-782", "status": "queued" }
```

#### API 2 — Search

```http
POST /search
```

Input: `image, text, category, latitude, longitude, radius`

```text
Request → CLIP → FAISS → Top 20 → PostgreSQL
       → Filtering → Ranking → Top 5
```

```json
{
  "query_id": "QUERY-123",
  "results": [
    { "case_id": "CASE-101", "match_score": 0.92, "case_type": "lost_pet", "category": "cat", "distance_km": 2.4 },
    { "case_id": "CASE-087", "match_score": 0.87, "case_type": "lost_pet", "category": "cat", "distance_km": 4.8 }
  ]
}
```

#### API 3 — Match a case

For new **found** reports:

```http
POST /cases/{case_id}/find-matches
```

```text
Existing Case → Extract Features → FAISS
      → Metadata → PostGIS → Re-ranking → Top matches
```

#### API 4 — Get match results

```http
GET /cases/{case_id}/matches
```

```json
{
  "case_id": "CASE-104",
  "matches": [
    { "case_id": "CASE-031", "score": 0.94, "status": "possible_match" }
  ]
}
```

### Day 7 — Docker + Integration + Testing

#### Docker Compose environment

```text
Docker Compose
│
├── ai-service
├── postgres
└── redis (only if the worker architecture needs it)
```

Add Node.js to the same Compose environment later if desired.

#### AI service Dockerfile

```text
Python Base Image
       ↓
System Dependencies
       ↓
Python Dependencies
       ↓
Application Code
       ↓
Model Configuration
       ↓
FastAPI
```

```yaml
# docker/docker-compose.yml (conceptual)
services:
  ai-service:
    build: ../ai-service
    ports: ["8000:8000"]
    env_file: ../ai-service/.env
    depends_on:
      - postgres
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: lostify
      POSTGRES_USER: lostify
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ../database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
```

Do not add Redis unless the worker architecture needs it.

#### Environment files

Commit `.env.example`, never `.env`:

```text
DATABASE_URL=...
FAISS_INDEX_PATH=...
MODEL_DIR=...
UPLOAD_DIR=...
```

## 6. Week 06 API Specification

```text
GET    /health
POST   /cases
GET    /cases/{case_id}
POST   /search
POST   /cases/{case_id}/find-matches
GET    /cases/{case_id}/matches
GET    /jobs/{job_id}
```

Later:

```text
DELETE /cases/{case_id}
PATCH  /cases/{case_id}
POST   /cases/{case_id}/verify-match
```

## 7. Testing

Three levels:

### 7.1 Unit tests

```text
ranking_service:  test_score_calculation()
filtering_service: test_category_filter()
embedding_service: test_distance_calculation()
```

### 7.2 API tests

```text
GET  /health
POST /cases
POST /search
GET  /jobs/{id}
GET  /cases/{id}/matches
```

### 7.3 End-to-end test (most important)

```text
Flutter → Node.js → AI Service → PostgreSQL → FAISS → AI Models → Results
```

If this works, there is a real integration pipeline.

## 8. Security

Do not leave the AI service wide open.

```text
Node.js Backend → Authentication → AI Service
(not: Internet → AI Service)
```

Add:

```text
Request validation
File type validation
File size limits
Image sanitization
Rate limiting
Authentication between services
Secure environment variables
Error handling
Logging
No sensitive data in logs
```

### Image upload security

Never trust `filename`, `MIME type`, or `extension`.

- Validate actual content.
- Allowed types: JPEG, PNG, WEBP.
- Reasonable maximum file size.
- Guard against malformed images, decompression bombs, unexpected dimensions.

## 9. Observability

Log structured fields:

```text
request_id
case_id
job_id
model
processing_time
status
error
```

```text
INFO  case_id=CASE-104  stage=CLIP  duration=182ms
```

Never log:

```text
passwords
tokens
private credentials
unnecessary personal data
```

## 10. Performance Benchmark

Create `benchmark.py` and measure every stage:

```text
Upload time
Image preprocessing
YOLO
OCR
Face
CLIP
FAISS
PostgreSQL
Ranking
Total response
```

```text
-------------------------------
AI SERVICE BENCHMARK
-------------------------------
YOLO:          XX ms
OCR:           XX ms
Face:          XX ms
CLIP:          XX ms
FAISS:         XX ms
PostgreSQL:    XX ms
Ranking:       XX ms
-------------------------------
Total:         XX ms
-------------------------------
```

Use actual measurements.

## 11. Complete Production Pipeline

The main thing to implement during Week 06:

```text
                    USER
                     │
                     ▼
              Flutter / React
                     │
                     ▼
              Node.js Backend
                     │
             Create Lost Case
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
     PostgreSQL              AI Service
      + PostGIS                  │
                                 ▼
                         Image Processing
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
               YOLO             OCR             Face
                 │               │               │
                 └───────────────┼───────────────┘
                                 ▼
                                CLIP
                                 │
                                 ▼
                          Vector Embedding
                                 │
                                 ▼
                              FAISS
                                 │
                              Top 20
                                 │
                                 ▼
                           PostgreSQL
                                 │
                         Metadata Filter
                                 │
                                 ▼
                          PostGIS Filter
                                 │
                                 ▼
                          Re-ranking
                                 │
                                 ▼
                            Top 5
                                 │
                                 ▼
                          Match Records
                                 │
                                 ▼
                         Node.js Backend
                                 │
                  ┌──────────────┴─────────────┐
                  ▼                            ▼
              Flutter                       React
```

## 12. Week 06 Daily Plan

| Day | Focus | Main Deliverable |
| --- | --- | --- |
| Day 1 | FastAPI architecture | Production API skeleton |
| Day 2 | PostgreSQL + PostGIS | Database + spatial queries |
| Day 3 | FAISS service | Persistent vector search |
| Day 4 | Model serving | CLIP/YOLO/OCR/Face loaded once |
| Day 5 | Async processing | Job/worker pipeline |
| Day 6 | API integration | Case + search + matching APIs |
| Day 7 | Docker + testing | Full containerized AI service |

## 13. Week 06 Definition of Done

Week 06 is complete when all five tests pass:

**Test 1 — Create case**

```text
Flutter → Node.js → POST /cases → PostgreSQL → AI Job
```

**Test 2 — AI processing**

```text
Image → YOLO → OCR → Face → CLIP → FAISS → PostGIS → Ranking
```

**Test 3 — Get matches**

```text
GET /cases/{id}/matches → Top 5 candidates → Flutter
```

**Test 4 — Docker**

```bash
docker compose up
```

starts the required services.

**Test 5 — Failure handling**

```text
Invalid image
Huge image
Missing image
Database unavailable
FAISS unavailable
Model unavailable
Invalid coordinates
Invalid case type
```

The API returns controlled errors instead of crashing.

## 14. After Week 06

Lostify AI is no longer "a CLIP experiment". It has a real architecture:

```text
                  LOSTIFY AI
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Flutter       React        Node.js
                                    │
                                    ▼
                              Python AI
                                    │
             ┌──────────────────────┼──────────────────┐
             ▼                      ▼                  ▼
           Models                FAISS            PostgreSQL
             │                                       │
     ┌───────┼───────┐                               │
     ▼       ▼       ▼                               ▼
    CLIP    YOLO    OCR                         PostGIS
             │
           Face
```

**Week 07** naturally becomes **Full Lostify AI Integration + Event-Driven Matching + Notifications**, where a newly submitted lost/found case automatically triggers the AI matching pipeline and stores/returns candidate matches.