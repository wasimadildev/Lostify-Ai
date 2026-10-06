# 05-face — optimise the threshold, discover the corpus cannot support it

## The result

The threshold was not optimised, and that is the finding.

```text
faces detected       10 of 22 person cases
lost with a face       8
found with a face      2   (25% retained)
entities with both     2   ->  2 positive pairs against a 20-pair minimum
similarity span     0.7853 - 0.9864   (negative minimum 0.7853)
threshold           0.60  = dlib's documented default, unvalidated here
ranker weight       0.10  face corroborates, it never decides
```

## Files

| File | Purpose |
| --- | --- |
| `face_features.py` | Detect and embed every person face once; cache it. |
| `threshold_test.py` | Sweep 0.50-0.80, confusion matrix, P/R/F1, FAR, FRR, EER. |
| `evaluate.py` | Decide what ships, at what weight, and what is still missing. |

## The sweep, reported in full

Day 6 asks for the table, so here it is in full — with the number of positives
that makes it unreadable:

```text
    t   TP   FP   FN   TN    prec  recall     F1    FAR    FRR
0.50    2   43    0     0   0.044   1.000  0.085  1.000  0.000
0.60    2   43    0     0   0.044   1.000  0.085  1.000  0.000
0.70    2   43    0     0   0.044   1.000  0.085  1.000  0.000
0.80    2   41    0     2   0.046   1.000  0.089  0.954  0.000
EER 0.000 at threshold 0.9529
```

Two rows are read as: `recall 1.000` because both positives score above every
threshold tried, and `precision 0.044` because all 43 negatives also do.
EER 0.000 is arithmetically true and completely useless. Tuning here would be
fitting two points.

## Three separate reasons this failed

**1. Too few positives.** Only `PERS-07` and `PERS-08` have a detectable face on
both sides, so there are 2 positive pairs. The minimum this week sets is 20.

**2. The augmentation destroys the faces.** Found views apply
`crop+resize+flip+rotate+brightness+contrast+color`. Only 2 of 8 lost faces
survive it — 75% of true matches have no face to compare at all. The data
pipeline is removing the evidence the model needs.

**3. The classes are not separable.** Every one of the 45 pairwise similarities
lies between 0.7853 and 0.9864. dlib separates different people at roughly
0.0–0.4 and the same person above 0.6; a negative minimum of 0.7853 means the
negatives sit *inside* the same-person range. The dynamic range available to a
threshold is 0.20 wide, not the ~1.0 a real face corpus gives.

The two true positives are the top two scores in the matrix (0.9864, 0.9529), so
there is real signal — it is just compressed into a 0.13-wide band above a
background of 0.85.

## What ships instead

Nothing tuned. `evaluate.py` records `0.60` — dlib's documented default — and
labels it `validated_on_corpus: false` so no later reader can mistake a prior for
a measurement.

The ranker weights face evidence **0.10**, so it can corroborate a candidate but
never carry one. This is what the data supports: a signal that is 25% present
and 0.2-wide cannot be trusted with a decision.

To replace the prior, in order:

1. Exclude person cases from the face-destructive augmentation recipe.
2. Collect real second captures; a synthetic transform is not a re-photograph.
3. Re-run `threshold_test.py` at ≥20 entities with faces on both sides.

## Privacy

Face embeddings are biometric data and a special category under UK GDPR. The
week fine-tunes no face model, per Day 6. Embeddings cache locally under
`outputs/` and are never committed. Before production: encryption at rest,
access control with audit logging, explicit consent and a documented legal basis,
minimum retention, and no third-party transmission.