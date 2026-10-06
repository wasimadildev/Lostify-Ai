# 01-dataset — the Lostify AI case catalog

Everything in Week 05 is measured against this folder, so it is built first and
frozen before a single model is trained.

## Files

| File | Purpose |
| --- | --- |
| `cases.json` | The catalog: 92 reports over 46 real-world entities. Source of truth. |
| `train.json` / `validation.json` / `test.json` | Group-aware 70/15/15 split of `cases.json`. |
| `pairs.json` | Positive / negative match pairs for CLIP contrastive training. |
| `images/found/` | The rendered "found" view of each entity (generated, not hand-made). |

## Case schema

```json
{
  "case_id": "PETS-01",
  "entity_id": "ENT-PETS-01",
  "type": "lost_pet",
  "category": "cat",
  "top_level": "PET",
  "subcategory": "cat",
  "title": "White Persian Cat with Blue Collar",
  "description": "White Persian cat with a blue collar, lost near the park",
  "location": "Islamabad",
  "latitude": 33.6844,
  "longitude": 73.0479,
  "status": "lost",
  "report_date": "2026-08-28",
  "image": "../../Week-04/data/pets/PETS-01.jpg",
  "image_origin": "data/pets/PETS-01.jpg",
  "split": "train"
}
```

`entity_id` is the ground truth. Two cases match **if and only if** they share an
`entity_id`. Every downstream label — contrastive pair, ranker label, retrieval
expectation, face match decision — is derived from that one field.

## Taxonomy

```text
Top level:   PERSON  PET  ITEM  VEHICLE  DOCUMENT  OTHER

PET       → dog, cat, bird, rabbit, other
ITEM      → mobile, laptop, bag, wallet, watch, keys, bicycle, other
VEHICLE   → car, motorcycle, bicycle, other
```

The 46 curated photographs cover `PERSON`, `PET`, `ITEM` and `VEHICLE`.
`DOCUMENT` and `OTHER` are reserved but currently empty, so per-class metrics
are only reported for classes that actually have samples. Coverage is stated in
`outputs/metrics/dataset_statistics.json` rather than hidden.

## How the found reports are made

The product task is **lost report → found report**, so every entity needs two
reports. The source corpus holds exactly **one photograph per subject**, so a
genuine second capture is not available. `prepare_dataset.py --materialize`
therefore renders the found report from the same source photograph under a
deterministic recipe:

```text
crop (72–88% of frame) → resize (288–448 px) → optional horizontal flip
→ rotate ±14° → brightness / contrast / colour jitter → optional slight blur
```

The subject is identical, so the `entity_id` label is exact. Framing, scale,
orientation and photometry differ the way a second person's phone photo would,
which is precisely the invariance the retrieval model has to learn.

**This is the honest limitation of the benchmark.** Positives test
viewpoint/photometry invariance, *not* cross-session re-identification. A real
Lostify deployment faces the harder problem of two independent photographs of
the same person or pet, so absolute numbers here are optimistic. The protocol is
recorded in `cases.json` under `ground_truth_protocol` and repeated in every
results file so no reader can mistake it for real captured data.

## Split protocol — why it is grouped

```text
Dataset (46 entities)
    │
    ├── Train       32 entities  → 64 cases
    ├── Validation   7 entities  → 14 cases
    └── Test         7 entities  → 14 cases
```

The split is drawn over **entities, not images**. A random per-image split would
place the lost report of an entity in train and its found report in test, and the
model would be scored on a pair it had already memorised — textbook **data
leakage**. `validate_dataset.py` fails the build if any `entity_id` appears in
more than one split.

## Rebuild

```bash
python ../02-data-preparation/build_cases.py                      # cases.json from the Week 04 corpus
python ../02-data-preparation/prepare_dataset.py \
    --materialize --clean --split --pairs
python ../02-data-preparation/validate_dataset.py
python ../02-data-preparation/statistics.py
```