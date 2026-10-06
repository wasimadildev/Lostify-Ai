"""Rule-based re-ranking: weighted feature fusion with weights chosen on validation.

The roadmap says "Select weights through validation experiments, not
assumptions", and that strategy should depend on case type. Both are done here:
weights are searched per top-level category, scored on the *validation* split,
and the test split is touched only to report the result.

    python fusion.py

Writes outputs/metrics/fusion_weights.json.
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(WEEK05 / "02-data-preparation"))

from features import CONTINUOUS, FEATURES  # noqa: E402
from prepare_dataset import METRICS_DIR  # noqa: E402

REPORT = METRICS_DIR / "fusion_weights.json"

# Candidate weights per signal. 0.0 is included so the search can prove a
# feature is not worth using, which is the point of searching rather than
# assuming.
CANDIDATES = (0.0, 0.1, 0.2, 0.3, 0.4)
# Face weight ceiling comes from 05-face/evaluate.py: the signal is 25%
# present, 0.2-wide, and cannot carry a decision.
FACE_WEIGHTS = (0.0, 0.05, 0.1)


def fuse(row, weights):
    """Weighted mean over the signals that actually have evidence.

    A missing signal is dropped and the remaining weights renormalised, so a
    pet pair with no face is not punished for having no face.
    """
    total, weight_sum = 0.0, 0.0
    for name in CONTINUOUS:
        value = row["features"][name]
        weight = weights.get(name, 0.0)
        if value is None or weight <= 0.0:
            continue
        total += value * weight
        weight_sum += weight
    return total / weight_sum if weight_sum else 0.0


def roc_auc(labels, scores):
    """Rank-based AUC with proper tie handling; None when only one class."""
    labels = np.asarray(labels, dtype=float)
    scores = np.asarray(scores, dtype=float)
    positives, negatives = int((labels == 1).sum()), int((labels == 0).sum())
    if not positives or not negatives:
        return None
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=float)
    # Average ranks inside tied groups so ties do not inflate the score.
    for value in np.unique(scores):
        tied = np.flatnonzero(scores == value)
        if len(tied) > 1:
            ranks[tied] = ranks[tied].mean()
    return float((ranks[labels == 1].sum() - positives * (positives + 1) / 2)
                 / (positives * negatives))


def search(rows, feature_names, candidates=CANDIDATES):
    """Coordinate ascent over the weight grid, maximising validation AUC."""
    weights = {name: 0.0 for name in feature_names}
    best = roc_auc([r["label"] for r in rows], [fuse(r, weights) for r in rows])
    improved = True
    while improved:
        improved = False
        for name in feature_names:
            options = FACE_WEIGHTS if name == "face_score" else candidates
            for value in options:
                if value == weights[name]:
                    continue
                trial = dict(weights, **{name: value})
                auc = roc_auc([r["label"] for r in rows],
                              [fuse(r, trial) for r in rows])
                if auc is not None and (best is None or auc > best):
                    best, weights, improved = auc, trial, True
    return weights, best


def evaluate(rows, weights):
    labels = [r["label"] for r in rows]
    return {
        "pairs": len(rows),
        "positives": sum(labels),
        "fused_auc": roc_auc(labels, [fuse(r, weights) for r in rows]),
        "clip_only_auc": roc_auc(labels, [r["features"]["clip_score"] for r in rows]),
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()

    from features import build

    rows = build()["rows"]
    by_split = {
        split: [r for r in rows if r["split"] == split]
        for split in ("train", "validation", "test")
    }

    # Weights are searched per category on validation, then applied to test.
    per_category = {}
    for category in sorted({r["category"] for r in by_split["train"]}):
        valid_cat = [r for r in by_split["validation"] if r["category"] == category]
        test_cat = [r for r in by_split["test"] if r["category"] == category]
        if len({r["label"] for r in valid_cat}) < 2:
            per_category[category] = {
                "skipped": "validation split has a single class for this category",
                "validation_pairs": len(valid_cat),
            }
            continue
        weights, _ = search(valid_cat, CONTINUOUS)
        per_category[category] = {
            "weights": {k: v for k, v in weights.items() if v > 0},
            "validation": evaluate(valid_cat, weights),
            "test": evaluate(test_cat, weights),
        }

    overall, _ = search(by_split["validation"], CONTINUOUS)
    result = {
        "selection": "coordinate ascent on validation AUC; test is never searched",
        "candidate_weights": list(CANDIDATES),
        "face_weight_ceiling": list(FACE_WEIGHTS),
        "features": list(FEATURES),
        "overall": {
            "weights": {k: v for k, v in overall.items() if v > 0},
            "validation": evaluate(by_split["validation"], overall),
            "test": evaluate(by_split["test"], overall),
        },
        "per_category": per_category,
    }
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    _render(result)


def _render(result):
    overall = result["overall"]
    print("Rule-based fusion: weights chosen on validation")
    print("-" * 78)
    print("weights  " + "  ".join(f"{k}={v}" for k, v in overall["weights"].items())
          or "weights  (all zero)")
    for split in ("validation", "test"):
        row = overall[split]
        print(f"{split:>10}  fused AUC {row['fused_auc']:.4f}   "
              f"clip-only AUC {row['clip_only_auc']:.4f}   "
              f"({row['positives']}/{row['pairs']} positive)")
    print("-" * 78)
    for category, detail in result["per_category"].items():
        if "skipped" in detail:
            print(f"{category:8s} skipped: {detail['skipped']} "
                  f"({detail['validation_pairs']} validation pairs)")
            continue
        weights = "  ".join(f"{k}={v}" for k, v in detail["weights"].items()) or "(none)"
        test = detail["test"]
        print(f"{category:8s} {weights}")
        print(f"{'':8s} test fused AUC {test['fused_auc']}  "
              f"clip-only {test['clip_only_auc']}")


if __name__ == "__main__":
    main()