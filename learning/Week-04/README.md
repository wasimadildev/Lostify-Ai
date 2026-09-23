# Lostify AI - Week 04
## Specialized AI Models: YOLO + OCR + Face Recognition

### Week Objective

Week 03 made the matching engine accurate (filtering, ranking, multimodal search, evaluation). Week 04 makes Lostify AI **specialized**: it adds the AI models that understand *what is inside the image* instead of relying only on whole-image similarity.

Week 04 evolves the pipeline from:

```text
Image
  ↓
CLIP
  ↓
Similarity Search
  ↓
Top-5 Results
```

...into a pipeline that analyzes the image with dedicated models before matching:

```text
                      User Report
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Image        Text      Metadata
              │
              ▼
         Image Analysis
              │
       ┌──────┼──────────┐
       ▼      ▼          ▼
     YOLO    OCR    Face Detection
       │      │          │
       └──────┼──────────┘
              ▼
        Feature Extraction
              │
              ▼
        CLIP / Embeddings
              │
              ▼
           FAISS
              │
              ▼
        Candidate Cases
              │
              ▼
        Ranking Engine
              │
              ▼
        Top-5 Matches
```

## 1. Why Week 04 Needs More Than CLIP

CLIP answers one question very well:

> "How visually/semantically similar is this image to another?"

It does NOT answer:

- What objects are present and where?  → YOLO
- What text is readable in the image?   → OCR
- Is this the same person?              → Face Recognition

Week 04 adds these three capabilities. Each has one clear job:

| Model | Answers | Example output |
| --- | --- | --- |
| YOLO | "What objects are present and where?" | `dog, 0.94, [120, 80, 540, 620]` |
| OCR | "What text is in the image?" | `"WASEEM ADIL", 0.96` |
| Face Recognition | "Is this the same person?" | face embedding + similarity score |
| CLIP | "How similar is the whole image semantically?" | 512-D embedding |

**Important concept:** YOLO does not replace CLIP. They work together.

```text
YOLO  → structured visual information (objects + boxes)
CLIP  → semantic visual similarity (embedding matching)
```

## 2. Where Week 04 Starts (Foundation from Weeks 1-3)

### Week 01
- CLIP fundamentals, 512-D image embeddings, normalization, cosine similarity, Top-K.

### Week 02
- Precomputed `.npy` embeddings, FAISS `IndexFlatIP(512)`, FastAPI `POST /search`.

### Week 03
- Realistic dataset, metadata filtering, ranking service, combined score, multimodal (image + text) search, evaluation.

Week 04 keeps all of that and adds image *understanding* on top:

```text
CLIP + FAISS + Filtering + Ranking + Evaluation + API   (Week 03)
                    + YOLO + OCR + Face                 (Week 04)
```

## 3. Week 04 Plan (Day by Day)

### Day 1 - YOLO Fundamentals

Understand object detection and how it differs from classification.

```text
Classification            Object Detection
Image                     Image
  ↓                         ↓
"Cat"                    Cat  Bounding Box  Confidence
```

```json
{
  "class": "cat",
  "confidence": 0.94,
  "bbox": [120, 80, 540, 620]
}
```

Concepts to learn:
- Object detection, bounding boxes, classes, confidence score
- IoU (Intersection over Union)
- NMS (Non-Maximum Suppression)
- Precision, Recall, mAP
- YOLO architecture, pretrained models, inference vs training

Practical work:

```bash
pip install ultralytics
```

```text
image
  ↓
YOLO
  ↓
detections
  ↓
bounding boxes
  ↓
confidence
```

Deliverable: `01-yolo/detect.py` - load model, load image, run inference, print detections, save annotated image.

### Day 2 - YOLO for Lostify AI

Apply YOLO to the actual FYP use case. Lostify-relevant classes:

```text
person  dog  cat  car  motorcycle
bag     phone  laptop  backpack  bicycle
```

(Exact classes depend on the selected pretrained model/dataset.)

Example input: a lost-dog photo.

```text
dog       0.94
person    0.72
backpack  0.51
```

Extract structured features:

```json
{
  "objects": [
    { "class": "dog", "confidence": 0.94 }
  ]
}
```

### Day 3 - OCR Pipeline

OCR matters for lost items with identifiable text:

```text
ID card  license plate  school bag  phone
wallet   book           luggage     vehicle
name tag                 address label
```

Learn: text detection, text recognition, bounding boxes, confidence, image preprocessing, perspective correction, noise removal.

Recommended start: **PaddleOCR / PP-OCR** (pretrained) rather than training an OCR model from scratch.

```text
Image
  ↓
Preprocessing
  ↓
OCR
  ↓
Detected Text
  ↓
Confidence
  ↓
Structured Metadata
```

```json
{
  "text": [
    { "value": "WASEEM ADIL", "confidence": 0.96 },
    { "value": "MULTAN", "confidence": 0.91 }
  ]
}
```

Deliverable: `02-ocr/ocr.py`.

### Day 4 - OCR + Lostify Search

Connect OCR to the existing search engine.

Example report: lost black backpack whose image contains `STMU` and `WASEEM`.

```text
Visual:  black backpack
OCR:     STMU, WASEEM

Image
  ├── CLIP → visual embedding
  └── OCR  → extracted text → metadata matching
```

OCR text becomes an additional strong identifier during matching.

### Day 5 - Face Detection and Face Recognition

One of the most important parts of Lostify AI. Understand the distinction:

```text
Face Detection          Face Recognition
Where is the face?      Is this the same face?
Image                    Face
  ↓                        ↓
Face                      Face Embedding
Bounding Box               ↓
                          Vector
                            ↓
                          Similarity
```

Learn: detection, alignment, embeddings, cosine similarity, verification vs identification, thresholds, false positives, false negatives.

```text
Person Image
  ↓
Face Detection
  ↓
Face Crop
  ↓
Face Recognition Model
  ↓
Face Embedding
  ↓
Similarity Search
```

**Important architecture decision:** do NOT put face embeddings into the same FAISS index as CLIP embeddings - they live in different embedding spaces. Use separate indexes and combine at the ranking layer:

```text
                 Lostify AI
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    CLIP Index   Face Index   OCR Index
        │            │            │
    512/other      Face Emb.    Text
    dimensions     dimensions
```

### Day 6 - Unified AI Feature Extraction

Create a single extractor that combines everything:

```text
                    IMAGE
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
      YOLO           OCR          Face Model
       │              │              │
       ▼              ▼              ▼
   Objects          Text         Face Embeddings
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ▼
               Feature Store
                      │
                      ▼
              Matching Engine
```

Input: one image. Output:

```json
{
  "objects": [],
  "faces": [],
  "ocr_text": [],
  "clip_embedding": [],
  "face_embeddings": []
}
```

Deliverable: `04-feature-extraction/feature_extractor.py`.

### Day 7 - Build the First Specialized AI Pipeline

Integrate everything into one pipeline:

```text
1. Receive image
2. Validate image
3. YOLO detection
4. OCR
5. Face detection
6. CLIP embedding
7. Search existing indexes
8. Collect candidates
9. Rank candidates
10. Return results
```

Deliverable: `05-ai-pipeline/pipeline.py`.

## 4. Week 04 Folder Structure

```text
learning/Week-04/
│
├── README.md
│
├── 01-yolo/
│   ├── README.md
│   ├── detect.py            # load model, infer, print, save annotated image
│   ├── visualize.py         # draw bounding boxes on images
│   └── outputs/
│
├── 02-ocr/
│   ├── README.md
│   ├── ocr.py               # PaddleOCR/PP-OCR extraction
│   └── outputs/
│
├── 03-face/
│   ├── README.md
│   ├── detect_faces.py      # locate + crop faces
│   ├── generate_embeddings.py # face embeddings
│   └── outputs/
│
├── 04-feature-extraction/
│   ├── README.md
│   └── feature_extractor.py # unified objects + faces + ocr + embeddings
│
├── 05-ai-pipeline/
│   ├── README.md
│   └── pipeline.py          # full image -> candidates -> ranked results
│
└── evaluation/
    ├── test_dataset.json
    ├── evaluate.py
    └── results.json
```

## 5. Week 04 Final Architecture

```text
                         LOSTIFY AI
                             │
                             ▼
                       User Report
                             │
                ┌────────────┴────────────┐
                │                         │
              Image                      Text
                │                         │
                ▼                         ▼
        ┌────────────────┐              CLIP
        │ Image Analysis │                │
        └────────────────┘                │
                │                         │
       ┌────────┼────────┐                │
       ▼        ▼        ▼                │
     YOLO      OCR     Face               │
       │        │        │                │
       ▼        ▼        ▼                ▼
   Objects    Text    Face Emb.      Text Embedding
       │        │        │                │
       └────────┴────────┴────────────────┘
                        │
                        ▼
                 Candidate Retrieval
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      CLIP FAISS    Face FAISS    Metadata/OCR
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  Ranking Engine
                        │
                        ▼
                  Top 5 Matches
                        │
                        ▼
                     FastAPI
                        │
                        ▼
                    Flutter App
```

## 6. Week 04 Evaluation

Measure each model separately, then the whole system.

```text
evaluation/
├── test_dataset.json
├── evaluate.py
└── results.json
```

### YOLO
- Detection accuracy, precision, recall, mAP
- Inference time

### OCR
- Text detection, recognition accuracy, confidence
- Processing time

### Face
- Verification accuracy, false acceptance, false rejection
- Similarity threshold

### Complete system (most important)
- Top-1 matching accuracy
- Top-5 matching accuracy
- Average response time

## 7. What You Should NOT Do This Week

Avoid training everything from scratch:

```text
❌ Train YOLO from scratch
❌ Train CLIP from scratch
❌ Train face recognition from scratch
❌ Build your own OCR model
❌ Build a huge dataset
```

Instead:

```text
Pretrained Model
       ↓
Understand
       ↓
Run inference
       ↓
Integrate
       ↓
Evaluate
       ↓
Only then consider fine-tuning
```

## 8. Week 04 Deliverables Checklist

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | `01-yolo/detect.py` - YOLO detection experiment |  |
| 2 | YOLO applied to Lostify classes (person, dog, cat, bag, phone...) |  |
| 3 | `02-ocr/ocr.py` - OCR text extraction pipeline |  |
| 4 | OCR text integrated into matching/metadata |  |
| 5 | `03-face/` - face detection + embeddings |  |
| 6 | `04-feature-extraction/feature_extractor.py` - unified extraction |  |
| 7 | `05-ai-pipeline/pipeline.py` - integrated pipeline |  |
| 8 | `evaluation/` - per-model and system metrics |  |

## 9. Week 04 Outcome (Definition of Done)

At the end of Week 04, Lostify AI has an image-analysis layer on top of the Week 03 matching engine:

```text
Image Analysis (YOLO + OCR + Face) -> Feature Extraction -> FAISS
        -> Candidate Retrieval -> Ranking -> API
```

- The system knows what objects are in a photo, not just that the photo is similar.
- OCR text and face embeddings are captured and searchable.
- CLIP, face, and OCR use their own indexes and are combined at ranking.
- Per-model and end-to-end metrics are recorded.
- The API still serves the frontend with top-5 matches.

Only after this pipeline is solid should fine-tuning ever be considered.