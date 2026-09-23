# Lostify AI - Week 05
## Model Fine-Tuning & Better Matching — Complete Roadmap

### Week Objective

Week 05 is where the project moves from:

> "I can run pretrained AI models"

to:

> "I have adapted and evaluated models for the Lostify AI problem."

Weeks 01-04 added models and assembled the pipeline. Week 05 improves **accuracy** rather than adding more AI models. It turns the system from a generic similarity engine into a domain-adapted matching engine whose improvement is backed by measured results.

```text
Week 01 → AI + CLIP fundamentals
Week 02 → Embeddings + FAISS + API
Week 03 → Filtering + ranking + evaluation
Week 04 → YOLO + OCR + Face Recognition
Week 05 → Fine-tuning, threshold optimization & re-ranking (measured)
```

### The Week 05 Loan

> "Fine-tuning should only be done when your baseline evaluation shows a real domain gap and you have enough labeled data to justify it."

When that is not true, threshold optimization, better data, candidate filtering, and re-ranking produce a more defensible improvement with far less training complexity. Week 05 is therefore an **experimentation and evaluation week first**, and a "fine-tune-everything" week second.

## 1. Week 05 Target Architecture

```text
                    LOSTIFY AI
                        │
                        ▼
                    User Report
                        │
                ┌───────┴────────┐
                ▼                ▼
              Image             Text
                │                │
                ▼                ▼
          Image Analysis       CLIP
                │                │
       ┌────────┼────────┐       │
       ▼        ▼        ▼       │
      YOLO     OCR     Face      │
       │        │        │       │
       └────────┴────────┴───────┘
                        │
                        ▼
                 Feature Extraction
                        │
                        ▼
              Candidate Retrieval
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          CLIP       Face       Metadata
          FAISS      FAISS      Search
             │          │          │
             └──────────┼──────────┘
                        ▼
                 Re-ranking Model
                        │
                        ▼
                 Top-5 Matches
                        │
                        ▼
                   Evaluation
                        │
                        ▼
                 Improved Model
```

The change from Week 04: a **re-ranking model** sits between candidate retrieval and the top-5, and a **closing evaluation loop** measures whether the improved model is actually better.

## 2. Week 05 Project Structure

```text
learning/Week-05/
│
├── README.md
│
├── 01-dataset/
│   ├── README.md
│   ├── cases.json
│   ├── train.json
│   ├── validation.json
│   └── test.json
│
├── 02-data-preparation/
│   ├── prepare_dataset.py
│   ├── validate_dataset.py
│   └── statistics.py
│
├── 03-yolo/
│   ├── README.md
│   ├── dataset.yaml
│   ├── train.py
│   ├── validate.py
│   └── inference.py
│
├── 04-clip/
│   ├── README.md
│   ├── baseline.py
│   ├── prepare_pairs.py
│   ├── train.py
│   └── evaluate.py
│
├── 05-face/
│   ├── README.md
│   ├── threshold_test.py
│   └── evaluate.py
│
├── 06-ranking/
│   ├── README.md
│   ├── feature_builder.py
│   ├── train_ranker.py
│   └── rank.py
│
├── 07-evaluation/
│   ├── evaluate_all.py
│   ├── baseline_results.json
│   └── improved_results.json
│
└── outputs/
    ├── models/
    ├── metrics/
    └── graphs/
```

## 3. Week 05 Plan (Day by Day)

### Day 1 — Dataset Engineering

**The most important day of Week 05.** A model cannot learn from random images, so build a proper dataset before touching any model.

#### 3.1.1 Define the Lostify categories

Top level:

```text
PERSON
PET
ITEM
VEHICLE
DOCUMENT
OTHER
```

Subcategories:

```text
Pets:    dog  cat  bird  rabbit  other
Items:   mobile  laptop  bag  wallet  watch  keys  bicycle  other
Vehicles: car  motorcycle  bicycle  other
```

#### 3.1.2 Create the case dataset

```json
{
  "case_id": "CASE-0001",
  "type": "lost_pet",
  "category": "cat",
  "image": "images/cat_001.jpg",
  "description": "White Persian cat with blue collar",
  "location": "Islamabad",
  "status": "lost"
}
```

#### 3.1.3 Create matching pairs (essential for CLIP evaluation)

```text
Query Image                  Candidate               Label
─────────────────────────────────────────────────────────────
cat_001.jpg                  cat_001.jpg              MATCH
cat_001.jpg                  cat_002.jpg              NON-MATCH
cat_001.jpg                  dog_001.jpg              NON-MATCH
cat_001.jpg                  bag_001.jpg              NON-MATCH
```

```json
{ "query": "cat_001.jpg", "candidate": "cat_001.jpg", "label": 1 }
{ "query": "cat_001.jpg", "candidate": "dog_001.jpg", "label": 0 }
```

#### 3.1.4 Train / validation / test split

```text
Dataset
   │
   ├── Train       70%
   ├── Validation  15%
   └── Test        15%
```

**Do not blindly use a random split** if multiple images belong to the same real-world case/person/pet. Keep related images in the same split to avoid **data leakage**.

### Day 2 — Data Cleaning & Augmentation

#### 3.2.1 Remove bad samples

```text
❌ Corrupted images
❌ Duplicate images
❌ Extremely low-quality images
❌ Incorrect labels
❌ Irrelevant images
```

#### 3.2.2 Augmentation (experiment)

```text
Horizontal flip   Rotation          Brightness
Contrast          Crop              Resize
Blur              Noise
```

Avoid unrealistic transformations. A heavy transform that changes the identity of a person's face is inappropriate for a face dataset.

#### 3.2.3 Dataset statistics (`statistics.py`)

Report:

```text
Total images
Images per category
Images per class
Train count
Validation count
Test count
Average image resolution
Missing metadata
Duplicate images
```

Example:

```text
Total Images: 850

Pets:       300
Persons:    250
Items:      200
Vehicles:   100

Train: 595
Validation: 128
Test: 127
```

### Day 3 — Establish the Baseline

**Do not fine-tune yet.** First measure how the current pretrained system performs, so there is something to compare against.

```text
Pretrained CLIP
       ↓
Embedding
       ↓
FAISS
       ↓
Top-K
```

Measure:

```text
Retrieval   Top-1 / Top-5 / Top-10 accuracy
Ranking     MRR, Recall@K, Precision@K
Speed       embedding time, FAISS search time, total API time
```

Save `outputs/metrics/baseline_results.json`:

```json
{
  "model": "openai/clip-vit-base-patch32",
  "top_1": 0.61,
  "top_5": 0.78,
  "top_10": 0.86,
  "average_search_ms": 35
}
```

These numbers are examples only — use the actual measurements.

### Day 4 — YOLO Fine-Tuning

Fine-tune YOLO **only if** the Lostify detection classes require it (e.g. `lost_bag`, `lost_wallet`, `lost_phone`, `lost_laptop` are not distinguished enough by the pretrained model). Do not fine-tune just because it is on the roadmap.

```text
yolo_dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── dataset.yaml
```

```yaml
path: ./yolo_dataset

train: images/train
val: images/val
test: images/test

names:
  0: phone
  1: wallet
  2: bag
  3: laptop
```

Training script flow:

```text
Load pretrained YOLO
        ↓
Load Lostify dataset
        ↓
Train (start small, iterate fast)
        ↓
Validate
        ↓
Save best checkpoint
```

Evaluate and compare:

```text
Precision  Recall  mAP50  mAP50-95  Inference time
Pretrained YOLO   VS   Fine-tuned YOLO
```

### Day 5 — CLIP Fine-Tuning / Domain Adaptation

The most important part for the **matching engine**. Current CLIP understands general image-text relationships; Lostify needs *lost item A ↔ found item A* relatedness.

Objective: make related cases closer in embedding space.

```text
Lost item A   ↕   Found item A
```

Start with a frozen baseline, then fine-tune selected layers, then compare:

```text
Baseline
   ↓
Frozen CLIP
   ↓
Partial fine-tuning
   ↓
Evaluation
```

#### Training data: positive and negative pairs

```text
Positive pairs:
white-cat-01.jpg      white-cat-02.jpg
black-wallet-01.jpg   black-wallet-02.jpg
red-bike-01.jpg       red-bike-02.jpg

Negative pairs:
white-cat-01.jpg      dog-01.jpg
black-wallet-01.jpg   laptop-01.jpg
red-bike-01.jpg       car-01.jpg
```

#### Contrastive learning concept

```text
Positive pair  →  make embeddings closer
Negative pair  →  make embeddings farther apart
```

```text
Before:                          After:
Cat A ●              ● Cat B     Cat A ●● Cat B
(related cats apart)             (related cats close)

Unrelated stay separated:
Cat ●                ● Car
```

#### Training pipeline

```text
Training Dataset
      ↓
Image Pair
      ↓
CLIP Encoder
      ↓
Embedding A / Embedding B
      ↓
Similarity
      ↓
Contrastive Loss
      ↓
Backpropagation
      ↓
Updated Model
```

### Day 6 — Face Recognition Optimization

**Do not immediately fine-tune the face model.** First optimize the matching threshold.

Test candidate thresholds:

```text
0.50  0.55  0.60  0.65  0.70  0.75  0.80
```

Build a confusion matrix:

```text
                 Actual
              Match  Non-Match
Pred Match      TP       FP
Pred NonMatch  FN       TN
```

Calculate:

```text
Precision
Recall
F1
False Acceptance Rate (FAR)
False Rejection Rate (FRR)
```

For the FYP this is much more meaningful than "face recognition works".

#### Face recognition privacy

Face embeddings are sensitive biometric data. The eventual system should include:

```text
Access control
Encryption
Minimal retention
Consent / legal basis where applicable
Audit logs
Secure API
```

For the FYP prototype, clearly document the intended scope and limitations.

### Day 7 — Build the Re-Ranking Engine

All Week 04 models become one intelligent matching system. Instead of `CLIP score = final score`:

```text
Candidate
    │
    ├── CLIP similarity
    ├── Face similarity
    ├── OCR similarity
    ├── Object similarity
    ├── Category match
    ├── Location relevance
    └── Time relevance
          │
          ▼
      Re-ranking
          │
          ▼
       Final Score
```

Example feature vector for one candidate:

```json
{
  "clip_score": 0.89,
  "face_score": 0.93,
  "ocr_score": 0.80,
  "object_score": 0.95,
  "category_match": 1,
  "location_score": 0.75,
  "time_score": 0.80
}
```

#### Step 1 — Rule-based re-ranking baseline

```text
Final Score =
    CLIP × weight
  + Face × weight
  + OCR × weight
  + Object × weight
  + Location × weight
  + Time × weight
```

Select weights through validation experiments, not assumptions. Strategy can depend on case type:

```text
Person case:  face similarity is the strong signal
Pet case:     visual similarity is the strong signal
Item with serial/name:  OCR is the strong signal
```

#### Step 2 — Learned ranker

Once enough labeled examples exist, train a simple model:

```text
Logistic Regression   Random Forest   XGBoost
```

Input features: `clip_score, face_score, ocr_score, object_score, location_score, time_score, category_match`
Output: `match probability`

```text
                  Candidate
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      CLIP         Face          OCR
      0.89         0.93          0.80
        │            │             │
        └────────────┼─────────────┘
                     ▼
                Ranker Model
                     │
                     ▼
               Match Score
                     │
                     ▼
                  Top 5
```

This re-ranking engine becomes one of the strongest parts of the FYP.

## 4. Evaluation — The Most Important Part

Compare at the end of Week 05 (**use actual test data, never invent values**):

| System | Top-1 | Top-5 | Top-10 |
| --- | ---: | ---: | ---: |
| CLIP baseline | Actual | Actual | Actual |
| + Filtering | Actual | Actual | Actual |
| + YOLO features | Actual | Actual | Actual |
| + OCR | Actual | Actual | Actual |
| + Face | Actual | Actual | Actual |
| + Re-ranking | Actual | Actual | Actual |

### 4.1 Also measure latency

```text
Image upload  →  YOLO  →  OCR  →  Face  →  CLIP  →  FAISS  →  Ranking  →  API response
```

```text
YOLO:        XX ms
OCR:         XX ms
Face:        XX ms
CLIP:        XX ms
FAISS:       XX ms
Ranking:     XX ms
────────────────────
Total:       XX ms
```

A system that takes 30 seconds per search is not useful.

### 4.2 Create evaluation graphs

```text
outputs/graphs/
```

- Graph 1: Top-1 Accuracy, Baseline vs Improved
- Graph 2: Top-5 Accuracy, Baseline vs Improved
- Graph 3: Inference Time, model comparison
- Graph 4: Precision / Recall curves

These graphs directly feed the FYP report and presentation.

## 5. What to Learn This Week

### Machine Learning
- Training, validation, testing
- Overfitting, underfitting, data leakage
- Data augmentation
- Hyperparameters, learning rate, batch size
- Epoch, checkpoint, early stopping

### Computer Vision
- Transfer learning, fine-tuning
- Object detection
- Embeddings, metric learning
- Contrastive learning
- Face recognition, OCR

### Retrieval
- Vector search
- Recall@K, Precision@K, MRR
- Re-ranking, candidate generation
- Threshold optimization

## 6. Week 05 Daily Schedule

| Day | Main Work | Deliverable |
| --- | --- | --- |
| Day 1 | Dataset engineering | Train / val / test datasets |
| Day 2 | Cleaning + augmentation | Validated dataset |
| Day 3 | Baseline evaluation | `baseline_results.json` |
| Day 4 | YOLO fine-tuning | Fine-tuned detector |
| Day 5 | CLIP fine-tuning | Improved embedding model |
| Day 6 | Face/OCR optimization | Thresholds + metrics |
| Day 7 | Re-ranking engine | Unified matching system |

## 7. Week 05 Architecture (Repository Layout)

```text
learning/
│
├── Week-01/
├── Week-02/
├── Week-03/
├── Week-04/
└── Week-05/
    │
    ├── README.md
    ├── 01-dataset/            cases.json · train.json · validation.json · test.json
    ├── 02-data-preparation/   prepare_dataset.py · validate_dataset.py · statistics.py
    ├── 03-yolo/               dataset.yaml · train.py · validate.py · inference.py
    ├── 04-clip/               baseline.py · prepare_pairs.py · train.py · evaluate.py
    ├── 05-face/               threshold_test.py · evaluate.py
    ├── 06-ranking/            feature_builder.py · train_ranker.py · rank.py
    ├── 07-evaluation/         evaluate_all.py · baseline_results.json · improved_results.json
    └── outputs/               models/ · metrics/ · graphs/
```

## 8. Week 05 Definition of Done

Do not consider Week 05 complete until this can be demonstrated:

```text
               USER UPLOADS IMAGE
                        │
                        ▼
                Feature Extraction
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
        YOLO           OCR           Face
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                       CLIP
                        │
                        ▼
                  FAISS Retrieval
                        │
                        ▼
                   Top 20 Cases
                        │
                        ▼
                  Feature Builder
                        │
                        ▼
                 Re-ranking Model
                        │
                        ▼
                  Top 5 Matches
                        │
                        ▼
             Confidence + Evidence
```

And, critically, the ability to show:

```text
Baseline  →  improvement  →  measured result
```

That is far stronger academically than "we fine-tuned YOLO/CLIP".

## 9. Week 05 Key Adjustment

Make Week 05 a **primarily experimentation/evaluation week**, not a "fine-tune every model" week:

1. Evaluate the baseline honestly first (Day 3).
2. Fine-tune a model **only** when evaluation shows a real domain gap **and** there is enough labeled data to justify it.
3. Otherwise prefer: threshold optimization, better data, candidate filtering, and re-ranking — higher impact, far less training complexity.

Week 06 continues from here with the **Production AI Service**: FastAPI + PostgreSQL/PostGIS + FAISS + model serving + Docker + asynchronous processing + API integration.