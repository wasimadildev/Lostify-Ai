"""Decide what face threshold ships, and at what weight.

threshold_test.py proved this corpus cannot tune a threshold: 2 positive pairs,
and every negative scoring above 0.6 inside dlib's same-person range. So this
script does not invent a number. It records the documented default as an
explicit prior, states what would be needed to replace it, and hands the ranker
a weight that reflects how weak the evidence is.

    python evaluate.py

Writes outputs/metrics/face_decision.json.
"""

import json
import sys
from pathlib import Path

WEEK05 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(WEEK05 / "02-data-preparation"))

from face_features import load_cache  # noqa: E402
from prepare_dataset import METRICS_DIR  # noqa: E402

REPORT = METRICS_DIR / "face_decision.json"
SWEEP = METRICS_DIR / "face_thresholds.json"

# dlib's documented default distance threshold, as cosine similarity.
DEFAULT_THRESHOLD = 0.60
# How much the ranker may lean on face evidence before real captures exist.
DEFAULT_WEIGHT = 0.10


def run():
    sweep = json.loads(SWEEP.read_text()) if SWEEP.exists() else {}
    cache = load_cache()
    cover = sweep.get("coverage", {})
    span = sweep.get("dynamic_range", {})

    validated = bool(cover.get("sufficient")) and not span.get("compressed", True)
    threshold = sweep.get("best_by_f1", DEFAULT_THRESHOLD) if validated else DEFAULT_THRESHOLD

    result = {
        "threshold": threshold,
        "threshold_source": "measured on this corpus" if validated
                            else "dlib documented default, unvalidated here",
        "validated_on_corpus": validated,
        "ranker_weight": DEFAULT_WEIGHT if not validated else None,
        "evidence": {
            "positive_face_pairs": cover.get("max_positive_pairs"),
            "min_positives_required": cover.get("min_positives_required"),
            "found_face_retention": cover.get("found_face_retention"),
            "similarity_span": span.get("span"),
            "negative_min": span.get("negative_min"),
            "compressed": span.get("compressed"),
            "faces_detected": cache["with_face"],
            "person_cases": cover.get("person_cases"),
        },
        "why_not_tuned": [
            f"only {cover.get('max_positive_pairs')} positive face pairs exist "
            f"against a {cover.get('min_positives_required')}-pair minimum",
            "the augmentation pipeline leaves a detectable face in only "
            f"{((cover.get('found_face_retention') or 0) * 100):.0f}% of found "
            "person views, so most true matches have no face to compare",
            "every negative scores above 0.6, inside dlib's same-person range, so "
            "the classes overlap and any threshold fits noise",
        ],
        "to_unblock": [
            "keep person cases out of the face-destructive augmentation recipe "
            "(crop+flip+rotate+colour) so found views keep their face",
            "collect real second captures of the same person; synthetic transforms "
            "cannot stand in for a genuine re-photograph",
            "re-run threshold_test.py once >=20 entities have faces on both sides",
        ],
        "policy": (
            "face evidence corroborates a candidate, it never decides one. The "
            f"ranker weights it {DEFAULT_WEIGHT} and requires the visual signal to "
            "carry the match on its own."
        ),
        "privacy": {
            "classification": "biometric data - special category under UK GDPR",
            "prototype_scope": (
                "local FYP evaluation only; embeddings cached under outputs/ and "
                "never committed"
            ),
            "required_before_production": [
                "encryption at rest for face embeddings",
                "access control and audit logging on every comparison",
                "explicit consent and a documented legal basis",
                "minimum retention with automatic deletion",
                "no third-party transmission of embeddings",
            ],
            "caveat": (
                "no face-detection model was fine-tuned or replaced in Week 05, "
                "per the Day 6 instruction to optimise the threshold first"
            ),
        },
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    return result


def render(result):
    evidence = result["evidence"]
    return "\n".join([
        "Face matching policy",
        "-" * 78,
        f"threshold            {result['threshold']:.2f}",
        f"source               {result['threshold_source']}",
        f"validated on corpus  {result['validated_on_corpus']}",
        f"ranker weight        {result['ranker_weight']}",
        "-" * 78,
        f"faces detected       {evidence['faces_detected']} of "
        f"{evidence['person_cases']} person cases",
        f"positive pairs       {evidence['positive_face_pairs']} "
        f"(need {evidence['min_positives_required']})",
        f"similarity span      {evidence['similarity_span']} "
        f"(negative minimum {evidence['negative_min']})",
        "-" * 78,
        *("  not tuned: " + line for line in result["why_not_tuned"]),
        "",
        f"policy: {result['policy']}",
        "",
        "before production: " + ", ".join(
            result["privacy"]["required_before_production"][:3]) + ", ...",
    ])


def main():
    print(render(run()))


if __name__ == "__main__":
    main()