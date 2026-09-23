# Lostify AI - Week 07
## Full System Integration + Event-Driven Matching + Notifications

### Week Objective

Week 07 is where the separate components become **one complete Lostify AI application**. Everything built so far is connected into a single, automatically reacting workflow:

```text
Week 1 → AI + CLIP fundamentals
Week 2 → Embeddings + FAISS
Week 3 → Filtering + Ranking + Evaluation
Week 4 → YOLO + OCR + Face Recognition
Week 5 → Fine-tuning + Better Matching
Week 6 → Production AI Service
Week 7 → Integration + Event-Driven Matching + Notifications
```

```text
Flutter
   ↓
Node.js Backend
   ↓
PostgreSQL/PostGIS
   ↓
Event
   ↓
AI Processing
   ↓
FAISS + Matching
   ↓
Match Created
   ↓
Notification
   ↓
User / NGO / Admin
```

### Week 07 Main Goal

By the end of the week, demonstrate the complete scenario:

> A user reports a lost pet/item/person → the case is stored → an event is generated → AI automatically processes the image → similar cases are searched → candidates are ranked → a potential match is created → the relevant user receives a notification → the user opens the match and can verify/report it.

This is the first real **end-to-end Lostify AI workflow**.

## 1. Target Architecture

```text
                         LOSTIFY AI
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
          ▼                                     ▼
       Flutter                              React Portal
       Mobile                                 Web
          │                                     │
          └──────────────────┬──────────────────┘
                             ▼
                      Node.js / Express
                       API Gateway
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
         PostgreSQL       Event System      Firebase
          + PostGIS           │             FCM
             │                │                │
             │                ▼                │
             │          AI Processing          │
             │                │                │
             │        ┌───────┴────────┐       │
             │        ▼                ▼       │
             │     Python AI        Matching   │
             │     Service           Engine    │
             │        │                │       │
             │   ┌────┼────┐           │       │
             │   ▼    ▼    ▼           ▼       │
             │ CLIP YOLO OCR/Face     FAISS     │
             │        │                │        │
             └────────┴────────────────┘        │
                      │                         │
                      ▼                         │
                 Match Created ────────────────┘
```

## 2. Week 07 Repository Structure

```text
learning/Week-07/
│
├── README.md
│
├── 01-integration/
│   ├── README.md
│   └── architecture.md
│
├── 02-events/
│   ├── README.md
│   ├── event-types.md
│   ├── event-publisher.js
│   └── event-consumer.py
│
├── 03-matching/
│   ├── matching-worker.py
│   ├── candidate-service.py
│   └── match-service.py
│
├── 04-notifications/
│   ├── notification-service.js
│   ├── firebase-service.js
│   └── templates/
│
├── 05-api/
│   ├── cases.md
│   ├── matches.md
│   ├── notifications.md
│   └── events.md
│
├── 06-flutter/
│   └── integration-notes.md
│
├── 07-testing/
│   ├── integration-tests/
│   ├── e2e-tests/
│   └── test-scenarios.md
│
└── 08-monitoring/
    ├── logs.md
    └── metrics.md
```

## 3. Week 07 Plan (Day by Day)

### Day 1 — Connect Flutter + Node.js + AI Service

Remove the idea of independent projects. The three tiers talk to each other:

```text
Flutter → Node.js → Python AI
```

#### Flutter → Node.js

Flutter must NOT directly manage the internal AI service. Everything goes through Node.js, which handles:

```text
Authentication   Authorization   Validation
Case creation    User ownership  File/storage handling
AI job creation
```

#### Node.js → AI Service

Node.js calls `POST /ai/process` or, preferably, creates an asynchronous processing job/event:

```text
Flutter
   │
   │ POST /cases
   ▼
Node.js
   │
   ├── Save case
   ├── Save image reference
   └── Publish event
            │
            ▼
         AI Worker
```

#### Case lifecycle

```text
DRAFT → SUBMITTED → PROCESSING → MATCHING → MATCHED / NO_MATCH → VERIFIED / CLOSED
```

```text
CASE-001  status = PROCESSING    →    CASE-001  status = MATCHED
```

### Day 2 — Event-Driven Architecture

The major topic of Week 07. Do not wait synchronously for AI:

```text
BAD:  Node.js → wait for AI → return response
GOOD: Node.js → Event → Worker
```

#### What is an event?

> Something happened.

Examples:

```text
CASE_CREATED
CASE_UPDATED
IMAGE_UPLOADED
AI_PROCESSING_STARTED
AI_PROCESSING_COMPLETED
MATCH_FOUND
MATCH_VERIFIED
NOTIFICATION_CREATED
```

When a user submits a lost cat, Node.js publishes:

```json
{
  "event": "CASE_CREATED",
  "case_id": "CASE-1001",
  "case_type": "lost_pet"
}
```

```text
CASE_CREATED → AI Worker → Extract Features → Search → Rank
```

#### Choose event infrastructure

Do not over-engineer. Options:

```text
Redis + worker        (simplest)
RabbitMQ              (broker; natural if the stack already uses RabbitMQ)
```

Start simple:

```text
Node.js → RabbitMQ → Python Worker
```

#### Consistent event structure

```json
{
  "event_id": "evt-123",
  "event_type": "CASE_CREATED",
  "timestamp": "2026-09-23T10:00:00Z",
  "source": "node-backend",
  "payload": { "case_id": "CASE-1001" }
}
```

**Why `event_id`?** Workers can receive the same message more than once. Recognizing `event_id = evt-123` and skipping a duplicate is called **idempotency**.

### Day 3 — Build the Automatic AI Matching Workflow

The most important workflow:

```text
USER SUBMITS CASE
       │
       ▼
CASE_CREATED → MESSAGE QUEUE → AI WORKER
       │
       ├── Download/read image
       ├── YOLO
       ├── OCR
       ├── Face
       ├── CLIP
       └── Metadata
       │
       ▼
FEATURES GENERATED → FAISS SEARCH → TOP 20 CANDIDATES
       │
       ▼
POSTGRESQL → FILTER → RE-RANK → TOP 5
       │
       ▼
MATCH_CREATED
```

#### Candidate retrieval

Do not compare the new case against every case. Use FAISS first, then filter:

```text
Top 20 → Category filter → Status filter → Location filter
       → Date filter → Re-ranking → Top 5
```

#### The matching matrix (prevent meaningless matches)

| New Case | Search Candidates |
| --- | --- |
| Lost Person | Found Person / Sightings |
| Lost Pet | Found Pet / Sightings |
| Lost Item | Found Item |
| Found Person | Lost Person |
| Found Pet | Lost Pet |
| Found Item | Lost Item |

### Day 4 — Match Service

Create a dedicated match service:

```text
Responsibilities:
candidate retrieval
similarity calculation
metadata filtering
location scoring
ranking
match persistence
```

#### Match table

```text
matches
──────────────────────────────
id
source_case_id
candidate_case_id
visual_score
face_score
ocr_score
object_score
location_score
final_score
status
created_at
updated_at
```

#### Match status

```text
POSSIBLE → NOTIFIED → VIEWED → CONFIRMED / REJECTED / EXPIRED
```

```text
CASE-1001 + CASE-087 → score = 0.91 → POSSIBLE
```

#### Never automatically declare a match

AI produces a **potential match**, not a certainty:

```text
AI → Potential Match → User / Authorized Reviewer → Confirm / Reject
```

This is especially important for face recognition and missing-person workflows.

### Day 5 — Notification System

Connect Firebase Cloud Messaging:

```text
Match Created → Notification Event → Notification Service → Firebase FCM → User Phone
```

#### Notification types

```text
NEW_MATCH
MATCH_UPDATED
CASE_STATUS_CHANGED
NEW_SIGHTING
CASE_RESOLVED
ADMIN_ALERT
```

Example: `CASE-1001` (lost cat) matches `CASE-1090` (found cat, 0.91) → `MATCH_FOUND` → notification:

> Possible match found for your lost cat report.

The notification deep-links to the match screen.

#### Notification database

```text
notifications
────────────────────
id
user_id
type
title
body
reference_type
reference_id
is_read
created_at
```

This supports both push and in-app history.

### Day 6 — Flutter Match Experience

#### Submitted

```text
✓ Report Submitted
AI is analyzing your report...
Case ID: CASE-1001
Status: Processing
```

#### Processing (real states only, no fake percentages)

```text
Image Analysis        ✓
Object Detection      ✓
Similarity Search     ⏳
Finding Potential Matches ⏳
```

#### Match found

```text
Potential Match Found
92% similarity
[Image]
Lost Cat · Islamabad · Distance: 2.4 km
[View Case]
```

Label it a **potential match**, not a confirmed identity.

#### Evidence breakdown

```text
Visual Similarity    92%
Object Similarity    94%
Location Relevance   82%
Text Similarity      —
Created: 23 Sep 2026
Distance: 2.4 km
```

This is far better than a single unexplained "92% AI".

#### User decision

```text
Does this appear to be your lost item?

[Yes, this is it]   → MATCH_CONFIRMED
[No, not a match]   → MATCH_REJECTED
```

### Day 7 — Full End-to-End Testing

Stop developing individual features; test the entire system.

#### Scenario 1 — Lost pet

```text
User → Flutter → Create Lost Pet → Node.js → PostgreSQL → CASE_CREATED
    → RabbitMQ → AI Worker → YOLO → CLIP → FAISS → PostGIS
    → Ranking → MATCH_CREATED → Notification → Flutter
```

#### Scenario 2 — Lost item with text (backpack with "STMU / WASEEM")

```text
Image → YOLO (backpack) → OCR (STMU/WASEEM) → CLIP → FAISS
    → Metadata → Ranking
```

#### Scenario 3 — Person report

```text
Image → Face Detection → Face Embedding → Face Candidate Search
    → Additional evidence → Potential match → Human/user verification
```

Do not let AI establish identity solely from a similarity score.

#### Scenario 4 — No match (important)

If no sufficiently relevant candidate exists, return a real result:

```json
{ "status": "NO_MATCH", "results": [] }
```

#### Scenario 5 — AI failure

Simulate model/database/queue/image failures. The original case must never be lost:

```text
Case:  SUBMITTED
AI:    FAILED
Retry: AVAILABLE
```

#### Retry architecture

```text
AI_PROCESSING_FAILED
   ↓
Retry → AI Worker (Attempt 1, 2, 3) → Permanent Failure
```

Use a retry limit. Do not retry forever.

## 4. Security for Week 07

### Authentication / authorization

```text
Flutter → JWT → Node.js
```

Users may only access cases they are allowed to access. User A touching CASE-B must be blocked (401/403).

### Service-to-service

Do not expose the Python AI service to the public internet:

```text
Internet → Node.js → Private AI Service
```

Use internal network, service authentication, timeouts, and request validation.

## 5. Observability

### Correlation ID

Create one `request_id` and pass it through every tier:

```text
Node.js → RabbitMQ → AI Worker → PostgreSQL → Notification
```

```text
REQ-001  CASE_CREATED             case=CASE-1001
REQ-001  AI_PROCESSING_STARTED
REQ-001  CLIP_COMPLETED           duration=180ms
REQ-001  FAISS_COMPLETED          candidates=20
REQ-001  MATCH_CREATED            candidate=CASE-1090 score=0.91
REQ-001  NOTIFICATION_SENT        user=USER-001
```

### Metrics to track

```text
Cases submitted            Cases processed
AI failures                Average AI processing time
FAISS search time          Matches generated
Potential matches viewed   Matches confirmed / rejected
Notifications sent        Notification failures
```

These feed directly into the FYP evaluation.

## 6. Integration Test Matrix

| Scenario | Expected Result |
| --- | --- |
| Valid lost case | Case created |
| Invalid image | Validation error |
| Large image | Rejected |
| AI success | Match pipeline runs |
| AI failure | Job marked failed |
| Retry | Processing resumes |
| Match found | Notification created |
| No match | No-match state |
| User confirms | Match confirmed |
| User rejects | Match rejected |
| Unauthorized access | 403/401 |
| Missing case | 404 |
| Database failure | Controlled error |

## 7. Final Event Flow

The main Week 07 implementation:

```text
                         USER
                           │
                           ▼
                     Flutter App
                           │
                     POST /cases
                           │
                           ▼
                    Node.js Backend
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
        PostgreSQL                  Image Storage
             │
             ▼
        CASE_CREATED → RabbitMQ → AI Worker
             │
     ┌───────┼────────┐
     ▼       ▼        ▼
   YOLO     OCR      Face
     │       │        │
     └───────┼────────┘
             ▼
            CLIP → FAISS → Top Candidates → PostgreSQL → PostGIS
             │
             ▼
        Re-ranking → MATCH_CREATED → Notification Service → Firebase FCM
             │
             ▼
          Flutter → Potential Match
             │
       ┌─────┴─────┐
       ▼           ▼
    Confirm      Reject
       │           │
       ▼           ▼
MATCH_CONFIRMED  MATCH_REJECTED
```

## 8. Week 07 Daily Schedule

| Day | Focus | Main Deliverable |
| --- | --- | --- |
| Day 1 | Flutter + Node + AI integration | Connected applications |
| Day 2 | Event-driven architecture | RabbitMQ/event pipeline |
| Day 3 | Automatic AI matching | End-to-end matching worker |
| Day 4 | Match service | Match persistence + lifecycle |
| Day 5 | Notifications | Firebase + notification system |
| Day 6 | Flutter UX | Processing + match screens |
| Day 7 | E2E testing + monitoring | Complete working workflow |

## 9. Final Week 07 Structure (Whole Project)

```text
Lostify-AI/
│
├── README.md
├── documentation/
├── learning/            (Week-01 … Week-07)
├── mobile/              Flutter
├── web/                 React
├── backend/             Node.js
├── ai-service/          FastAPI
├── database/            PostgreSQL + PostGIS
├── workers/             AI / event workers
├── infrastructure/      docker/ · nginx/
└── tests/
```

## 10. Week 07 Definition of Done

Demonstrate **one complete real workflow** with no manually started Python scripts:

```text
1.  Open Flutter
2.  Create Lost Report
3.  Upload image
4.  Submit
5.  Node.js stores case
6.  CASE_CREATED event
7.  AI worker automatically starts
8.  YOLO + OCR + Face + CLIP
9.  FAISS retrieves candidates
10. PostGIS filters candidates
11. Ranking engine calculates scores
12. Match stored in PostgreSQL
13. MATCH_CREATED event
14. Firebase notification
15. User receives notification
16. User opens Potential Match
17. User confirms/rejects
18. Match status updated
```

**No manual `python similarity_search.py`.**

**No manually running the matching script.**

**No manually sending the notification.**

The system reacts to the **case submission event automatically**.

## 11. After Week 07

Lostify AI becomes a genuine integrated system:

```text
        ┌───────────────────────────────┐
        │          LOSTIFY AI           │
        ├───────────────────────────────┤
        │  Flutter        React          │
        │     │             │            │
        │     └──────┬──────┘            │
        │            ▼                    │
        │       Node.js API               │
        │            │                    │
        │  PostgreSQL  Queue  Notifications
        │            │      │            │
        │            ▼      │            │
        │       AI Service  │            │
        │            │      │            │
        │     CLIP/YOLO/OCR/Face         │
        │            │                   │
        │            ▼                   │
        │          FAISS                 │
        │            │                   │
        │            ▼                   │
        │        Matching                │
        │            │                   │
        │            ▼                   │
        │     Potential Match            │
        │            │                   │
        │            ▼                   │
        │      Notification ─────────────┘
        └───────────────────────────────┘
```

**Project progression:**

```text
Week 1: Learn AI
Week 2: Build retrieval
Week 3: Improve matching
Week 4: Add specialized models
Week 5: Fine-tune / evaluate
Week 6: Productionize AI
Week 7: Integrate everything + event-driven automation
```

**Week 08** continues with production hardening: Docker deployment, CI/CD, security (OWASP ASVS), monitoring, model/version management, backups, load testing, and deployment to a VPS/cloud environment.