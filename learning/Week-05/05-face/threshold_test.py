"""Optimise the face-match threshold instead of fine-tuning the face model.

Week 05 Day 6 asks for a confusion matrix, precision, recall, F1, FAR and FRR
across candidate thresholds 0.50-0.80. It also says, in the same breath, not to
fine-tune the face model first. So this script sweeps the threshold and reports
what the sweep is actually worth on this corpus -- which turns out to be the
more important half of the answer.

    python threshold_test.py

Writes outputs/metrics/face_thresholds.json.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(WEEK05 / "02-data-preparation"))

from face_features import load_cache, pairs_for_cache, similarity, vector_of  # noqa: E402
from prepare_dataset import METRICS_DIR, is_found, load_cases  # noqa: E402

REPORT = METRICS_DIR / "face_thresholds.json"
THRESHOLDS = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80)
MIN_POSITIVES = 20


def score_pairs(records):
    """Every face-eligible pair, labelled by whether both sides share an entity."""
    positive_ids, negative_ids = pairs_for_cache(records)
    def scored(pairs):
        out = []
        for left, right in pairs:
            first, second = vector_of(records, left), vector_of(records, right)
            if first is None or second is None:
                continue
            out.append({
                "left": left,
                "right": right,
                "similarity": round(similarity(first, second), 4),
            })
        return out

    return scored(positive_ids), scored(negative_ids)


def confusion(positives, negatives, threshold):
    """TP/FP/FN/TN at one threshold. A prediction is 'match' when sim >= t."""
    tp = sum(1 for row in positives if row["similarity"] >= threshold)
    fn = len(positives) - tp
    fp = sum(1 for row in negatives if row["similarity"] >= threshold)
    tn = len(negatives) - fp
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def metrics_from(counts):
    tp, fp, fn, tn = counts["tp"], counts["fp"], counts["fn"], counts["tn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    far = fp / (fp + tn) if fp + tn else 0.0
    frr = fn / (fn + tp) if fn + tp else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if tp + fp + fn + tn else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "far": round(far, 4),
        "frr": round(frr, 4),
        "accuracy": round(accuracy, 4),
        "eer": None,
    }


def equal_error_rate(positives, negatives):
    """Threshold where FRR == FAR, found by sweeping every observed similarity."""
    candidates = sorted({row["similarity"] for row in positives} |
                        {row["similarity"] for row in negatives})
    best = None
    for threshold in candidates:
        row = metrics_from(confusion(positives, negatives, threshold))
        gap = abs(row["frr"] - row["far"])
        if best is None or gap < best[0]:
            best = (gap, threshold, row["frr"], row["far"])
    return {
        "threshold": best[1],
        "frr": round(best[2], 4),
        "far": round(best[3], 4),
    }


def sweep(positives, negatives):
    rows = []
    for threshold in THRESHOLDS:
        counts = confusion(positives, negatives, threshold)
        row = {"threshold": threshold, **counts, **metrics_from(counts)}
        rows.append(row)
    return rows


def coverage(records):
    """Why the sweep cannot be trusted: how few face positives this corpus has."""
    cases = {case["case_id"]: case for case in load_cases()}
    with_face = [cid for cid, rec in records.items() if rec["status"] == "ok"]
    lost = [cid for cid in with_face if not is_found(cases[cid])]
    found = [cid for cid in with_face if is_found(cases[cid])]
    entities_with_both = {
        cases[cid]["entity_id"] for cid in lost
    } & {cases[cid]["entity_id"] for cid in found}
    person = [case for case in load_cases()
              if str(case.get("category", "")).lower().startswith("person")]
    return {
        "person_cases": len(person),
        "lost_person_cases": sum(1 for case in person if not is_found(case)),
        "found_person_cases": sum(1 for case in person if is_found(case)),
        "lost_with_face": len(lost),
        "found_with_face": len(found),
        "found_face_retention": round(len(found) / len(lost), 4) if lost else None,
        "entities_with_both_faces": len(entities_with_both),
        "max_positive_pairs": len(entities_with_both),
        "min_positives_required": MIN_POSITIVES,
        "sufficient": len(entities_with_both) >= MIN_POSITIVES,
    }


def dynamic_range(positives, negatives):
    """How much room does the threshold actually have to work in?

    dlib separates different people at roughly 0.0-0.4 and the same person at
    0.6+. If every pair here -- match or not -- lands in a narrow high band, the
    threshold is fitting noise no matter what F1 says.
    """
    scores = [row["similarity"] for row in positives] + [
        row["similarity"] for row in negatives
    ]
    if not scores:
        return {"available": False}

    pos = [row["similarity"] for row in positives]
    neg = [row["similarity"] for row in negatives]
    return {
        "available": True,
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "span": round(max(scores) - min(scores), 4),
        "negative_min": round(min(neg), 4) if neg else None,
        "positive_min": round(min(pos), 4) if pos else None,
        "separation_gap": round(min(pos) - max(neg), 4) if pos and neg else None,
        "compressed": bool(neg and min(neg) > 0.6),
        "note": (
            "every negative scores above 0.6, which is dlib's same-person range; "
            "the negatives and positives occupy one narrow band, so the threshold "
            "is separating two nearly identical distributions rather than "
            "matching from non-matching"
        ) if neg and min(neg) > 0.6 else None,
    }


def run():
    records = load_cache()["records"]
    positives, negatives = score_pairs(records)
    cover = coverage(records)

    result = {
        "detector": "face_recognition (dlib, 128-d), largest face per image",
        "thresholds": sweep(positives, negatives),
        "coverage": cover,
        "dynamic_range": dynamic_range(positives, negatives),
        "positive_similarities": [row["similarity"] for row in positives],
        "negative_similarity": (
            {
                "count": len(negatives),
                "mean": round(float(np.mean([r["similarity"] for r in negatives])), 4)
                if negatives else None,
                "max": round(max((r["similarity"] for r in negatives), default=0.0), 4),
                "p99": round(float(np.percentile(
                    [r["similarity"] for r in negatives], 99)), 4) if negatives else None,
            }
        ),
    }

    if positives and negatives:
        result["equal_error"] = equal_error_rate(positives, negatives)
        best = max(result["thresholds"], key=lambda row: row["f1"])
        result["best_by_f1"] = best["threshold"]
        result["best_row"] = best
        # A threshold is only meaningful between the classes it must separate.
        result["separable"] = bool(
            max(row["similarity"] for row in negatives)
            < min(row["similarity"] for row in positives)
        )
    else:
        result["error"] = "no face-eligible pairs; run face_features.py"

    result["verdict"] = verdict(cover, result)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    return result


def verdict(cover, result):
    if not cover["sufficient"]:
        return (
            f"threshold NOT optimised: only {cover['max_positive_pairs']} positive "
            f"face pairs exist (need {MIN_POSITIVES}). The sweep below is "
            "reported for completeness and must not be used as a tuned value."
        )
    span = result.get("dynamic_range", {})
    if span.get("compressed"):
        return (
            "threshold NOT optimised: positives and negatives share one narrow "
            f"band ({span['min']}-{span['max']}, negative minimum "
            f"{span['negative_min']}), so no threshold is separating identities. "
            "Ship dlib's documented default and validate it on real captures."
        )
    if not result.get("separable", False):
        return (
            "threshold optimised, but the classes overlap: the negative "
            "similarity tail crosses the positive one, so no threshold gives a "
            "clean separation"
        )
    return f"threshold optimised to {result.get('best_by_f1')} on the measured sweep"


def render(result):
    cover = result["coverage"]
    lines = [
        "Face-match threshold sweep",
        "-" * 78,
        f"person cases                {cover['person_cases']} "
        f"({cover['lost_person_cases']} lost, {cover['found_person_cases']} found)",
        f"lost images with a face     {cover['lost_with_face']}",
        f"found views with a face     {cover['found_with_face']}"
        + (f"  ({cover['found_face_retention']:.1%} retained)"
           if cover["found_face_retention"] is not None else ""),
        f"entities with both faces    {cover['entities_with_both_faces']}"
        f"  -> {cover['max_positive_pairs']} positive pairs",
        "-" * 78,
        f"{'t':>5}{'TP':>5}{'FP':>5}{'FN':>5}{'TN':>6}"
        f"{'prec':>8}{'recall':>8}{'F1':>7}{'FAR':>7}{'FRR':>7}",
        "-" * 78,
    ]
    for row in result["thresholds"]:
        lines.append(
            f"{row['threshold']:>5.2f}{row['tp']:>5}{row['fp']:>5}{row['fn']:>5}"
            f"{row['tn']:>6}{row['precision']:>8.3f}{row['recall']:>8.3f}"
            f"{row['f1']:>7.3f}{row['far']:>7.3f}{row['frr']:>7.3f}"
        )
    lines.append("-" * 78)
    span = result.get("dynamic_range", {})
    if span.get("available"):
        lines.append(
            f"similarity span {span['min']}-{span['max']} (width {span['span']}); "
            f"negative min {span['negative_min']}  positive min {span['positive_min']}"
            f"  separation {span['separation_gap']}"
        )
        if span.get("compressed"):
            lines.append(
                "  ! every negative scores in dlib's same-person range "
                "(>0.6): the classes are not separable on this corpus"
            )
    if "equal_error" in result:
        eer = result["equal_error"]
        lines.append(
            f"EER {eer['frr']:.3f} at threshold {eer['threshold']:.4f} "
            f"(FAR {eer['far']:.3f} / FRR {eer['frr']:.3f})"
        )
        negatives = result["negative_similarity"]
        lines.append(
            f"negative similarity mean {negatives['mean']}  max {negatives['max']}"
            f"  p99 {negatives['p99']}"
        )
    lines += ["", f"verdict: {result['verdict']}"]
    return "\n".join(lines)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(render(run()))


if __name__ == "__main__":
    main()