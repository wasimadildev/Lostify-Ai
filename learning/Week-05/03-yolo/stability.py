"""Is the detector's evidence stable enough to be a ranking feature?

The Week 05 "found" view is a deterministic augmentation of the lost image, so
it stands in for the second capture. If the augmentation destroys the object
that made the original detectable, then `object_score` is not measuring item
similarity -- it is measuring how the augmentation was configured. That would
make object evidence a liability in the ranker, not a feature.

    python stability.py [--confidence 0.25]

Writes outputs/metrics/yolo_augmentation_stability.json.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

from prepare_dataset import METRICS_DIR, is_found, load_cases, resolve_image  # noqa: E402
from inference import ObjectExtractor, jaccard  # noqa: E402

REPORT = METRICS_DIR / "yolo_augmentation_stability.json"


def measure(confidence=0.25):
    cases = load_cases()
    found = [case for case in cases if is_found(case)]
    lost = [case for case in cases if not is_found(case)]
    source_of = {case["entity_id"]: case for case in lost}

    extractor = ObjectExtractor(confidence=confidence)
    detected_lost = sum(1 for case in lost if extractor.classes(resolve_image(case)))
    detected_found = sum(1 for case in found if extractor.classes(resolve_image(case)))

    rows = []
    for candidate in found:
        query = source_of[candidate["entity_id"]]
        left = extractor.bag(resolve_image(query))
        right = extractor.bag(resolve_image(candidate))
        rows.append({
            "entity_id": candidate["entity_id"],
            "lost_objects": dict(left),
            "found_objects": dict(right),
            "object_score": round(jaccard(left, right), 4),
            "status": (
                "both blank" if not left and not right
                else "lost blank" if not left
                else "found blank" if not right
                else "agree" if jaccard(left, right) == 1.0
                else "disagree"
            ),
        })

    tally = {}
    for row in rows:
        tally[row["status"]] = tally.get(row["status"], 0) + 1

    pairs = len(rows)
    agree = tally.get("agree", 0)
    return {
        "confidence": confidence,
        "lost_images": {
            "count": len(lost),
            "with_detection": detected_lost,
            "detection_rate": round(detected_lost / len(lost), 4) if lost else None,
        },
        "found_views": {
            "count": len(found),
            "with_detection": detected_found,
            "detection_rate": round(detected_found / len(found), 4) if found else None,
        },
        "true_pairs": {
            "count": pairs,
            "identical_object_score": agree,
            "identical_object_score_rate": round(agree / pairs, 4) if pairs else None,
            "mean_object_score": round(
                sum(row["object_score"] for row in rows) / pairs, 4
            ) if pairs else None,
            "breakdown": tally,
        },
        "retention": round(detected_found / detected_lost, 4) if detected_lost else None,
        "verdict": (
            "object evidence is unstable across the augmentation; weight it "
            "below CLIP or drop it"
            if pairs and agree / pairs < 0.75 else
            "object evidence is stable enough to be a ranking feature"
        ),
        "pairs": rows,
    }


def render(report):
    lost = report["lost_images"]
    found = report["found_views"]
    pairs = report["true_pairs"]
    lines = [
        "YOLO evidence stability across the found-view augmentation",
        "-" * 64,
        f"{'lost images with a detection':<42}{lost['with_detection']:>4}/{lost['count']}"
        f"  {lost['detection_rate']:>6.1%}",
        f"{'found views with a detection':<42}{found['with_detection']:>4}/{found['count']}"
        f"  {found['detection_rate']:>6.1%}",
        f"{'detections retained by augmentation':<42}{report['retention'] or 0:>10.1%}",
        "-" * 64,
        f"{'true pairs, identical object score':<42}{pairs['identical_object_score']:>4}"
        f"/{pairs['count']}  {pairs['identical_object_score_rate'] or 0:>6.1%}",
        f"{'mean object_score on true pairs':<42}{pairs['mean_object_score']:>10.3f}",
        "-" * 64,
        f"breakdown: {pairs['breakdown']}",
        f"verdict  : {report['verdict']}",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confidence", type=float, default=0.25)
    args = parser.parse_args()

    report = measure(args.confidence)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(render(report))


if __name__ == "__main__":
    main()