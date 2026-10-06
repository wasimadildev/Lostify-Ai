"""Assemble the fusion feature vector every ranker consumes.

Seven signals, exactly as the architecture diagram lists them: CLIP, face, OCR,
object, category, location and time. Each returns `None` when it has no
evidence for a candidate, and `None` is meaningful -- a missing face and a
score of zero are different facts, and the ranker must be able to tell them
apart rather than treating absence as a weak vote.

    python features.py          # dump outputs/metrics/ranker_features.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEEK05 / "02-data-preparation"))
sys.path.insert(0, str(WEEK05 / "03-yolo"))
sys.path.insert(0, str(WEEK05 / "04-clip"))
sys.path.insert(0, str(WEEK05 / "05-face"))
sys.path.insert(0, str(WEEK05 / "06-ranking"))

from clip_model import load_cache as load_clip_cache  # noqa: E402
from face_features import load_cache as load_face_cache  # noqa: E402
from inference import ObjectExtractor  # noqa: E402
from ocr_text import score_cases as ocr_score  # noqa: E402
from prepare_dataset import (  # noqa: E402
    METRICS_DIR,
    MODELS_DIR,
    is_found,
    load_cases,
    load_pairs,
    resolve_image,
    top_level_category,
)

REPORT = METRICS_DIR / "ranker_features.json"
DETECTIONS_CACHE = MODELS_DIR / "yolo" / "case_detections.json"

FEATURES = (
    "clip_score",
    "face_score",
    "ocr_score",
    "object_score",
    "category_match",
    "location_score",
    "time_score",
)
# category_match is a flag, so it is not rescaled into [0, 1].
CONTINUOUS = tuple(name for name in FEATURES if name != "category_match")


def _coerce_datetime(value):
    """Accept both `datetime` objects and ISO strings; return UTC-aware."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _cosine_table(cases, vectors, source, target):
    """All-vs-all cosine similarity between two groups of cases."""
    rows = {case["case_id"]: position for position, case in enumerate(cases)}
    left = np.asarray([vectors[rows[c["case_id"]]] for c in source], dtype=np.float32)
    right = np.asarray([vectors[rows[c["case_id"]]] for c in target], dtype=np.float32)
    matrix = left @ right.T
    return {
        (a["case_id"], b["case_id"]): float(matrix[i, j])
        for i, a in enumerate(source)
        for j, b in enumerate(target)
    }


def clip_scores(cases):
    embeddings, _ = load_clip_cache()
    return _cosine_table(cases, embeddings,
                         [c for c in cases if not is_found(c)],
                         [c for c in cases if is_found(c)])


def face_scores(cases):
    """Face cosine, only where both sides actually have a face."""
    records = load_face_cache()["records"]
    usable = [c for c in cases if records.get(c["case_id"], {}).get("status") == "ok"]
    if not usable:
        return {}
    vectors = np.asarray(
        [records[c["case_id"]]["embedding"] for c in usable], dtype=np.float32
    )
    return _cosine_table(cases, vectors, usable, usable)


def _class_bags(cases):
    """Detect once per case and cache to disk; YOLO is slow enough to matter."""
    if DETECTIONS_CACHE.exists():
        return json.loads(DETECTIONS_CACHE.read_text())

    extractor = ObjectExtractor()
    bags = {}
    for case in cases:
        bags[case["case_id"]] = sorted(set(extractor.classes(resolve_image(case))))
    payload = {"confidence": extractor.confidence, "classes": bags}
    DETECTIONS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    DETECTIONS_CACHE.write_text(json.dumps(payload, indent=2) + "\n")
    return payload["classes"]


def object_scores(cases):
    """Jaccard overlap of detected object classes, as Week 04 defined it."""
    bags = _class_bags(cases)
    out = {}
    for left in cases:
        a = set(bags.get(left["case_id"], []))
        for right in cases:
            b = set(bags.get(right["case_id"], []))
            union = a | b
            out[(left["case_id"], right["case_id"])] = (
                len(a & b) / len(union) if union else 0.0
            )
    return out


def location_score(left, right):
    """Exact match when both are known, else no evidence."""
    a, b = left.get("location"), right.get("location")
    if not a or not b:
        return None
    return 1.0 if str(a).strip().lower() == str(b).strip().lower() else 0.0


def time_score(left, right):
    """Proximity in time, 1.0 at the same instant, decaying to 0.0 at 90 days."""
    first = _coerce_datetime(left.get("reported_at"))
    second = _coerce_datetime(right.get("reported_at"))
    if first is None or second is None:
        return None
    days = abs((first - second).total_seconds()) / 86400.0
    return round(max(0.0, 1.0 - days / 90.0), 4)


def category_match(left, right):
    return 1 if top_level_category(left) == top_level_category(right) else 0


def build():
    cases = load_cases()
    by_id = {case["case_id"]: case for case in cases}
    pairs = load_pairs()
    clip = clip_scores(cases)
    faces = face_scores(cases)
    objects = object_scores(cases)

    rows = []
    for pair in pairs:
        left_id, right_id = pair["query_case"], pair["candidate_case"]
        left, right = by_id[left_id], by_id[right_id]
        ocr = ocr_score(left_id, right_id)
        rows.append({
            "pair_id": pair["pair_id"],
            "split": pair["split"],
            "label": pair["label"],
            "query_case": left_id,
            "candidate_case": right_id,
            "entity_id": left["entity_id"],
            "category": top_level_category(left),
            "hard_negative": pair.get("hard_negative", False),
            "features": {
                "clip_score": round(clip.get((left_id, right_id), 0.0), 4),
                "face_score": round(faces[(left_id, right_id)], 4)
                               if (left_id, right_id) in faces else None,
                "ocr_score": round(ocr, 4) if ocr is not None else None,
                "object_score": round(objects[(left_id, right_id)], 4),
                "category_match": category_match(left, right),
                "location_score": location_score(left, right),
                "time_score": time_score(left, right),
            },
        })

    return {
        "features": list(FEATURES),
        "continuous": list(CONTINUOUS),
        "pairs": len(rows),
        "positives": sum(1 for r in rows if r["label"] == 1),
        "availability": {
            name: {
                "present": sum(1 for r in rows if r["features"][name] is not None),
                "missing": sum(1 for r in rows if r["features"][name] is None),
            }
            for name in FEATURES
        },
        "rows": rows,
    }


def main():
    payload = build()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"ranker features: {payload['pairs']} pairs "
          f"({payload['positives']} positive)")
    for name, stat in payload["availability"].items():
        print(f"  {name:16s} present {stat['present']:>4}  missing {stat['missing']:>4}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()