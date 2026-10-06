"""Face embeddings for the Week 05 person cases, cached once.

Only `status == found` cases whose category is a person carry a usable face.
Everyone else contributes nothing, and pretending otherwise would let the ranker
weight a feature that has no evidence behind it.

    python face_features.py          # embed and cache every face it can find
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
DATASET_DIR = WEEK05 / "01-dataset"
CACHE_DIR = WEEK05 / "outputs" / "models" / "faces"

sys.path.insert(0, str(WEEK05 / "02-data-preparation"))
from prepare_dataset import load_cases, resolve_image, top_level_category  # noqa: E402

CACHE = CACHE_DIR / "face_embeddings.json"


class FaceEmbedder:
    """L2-normalised dlib/`face_recognition` embeddings, largest face first."""

    def __init__(self, model="hog"):
        try:
            import face_recognition
        except ImportError as exc:
            raise RuntimeError(
                "Face embeddings need face_recognition. See requirements-week05.txt."
            ) from exc
        self.backend = face_recognition
        self.model = model

    def embeddings(self, image_path):
        """Every face in the image; callers decide how many to keep."""
        array = np.asarray(_open_rgb(image_path))
        locations = self.backend.face_locations(array, model=self.model)
        found = self.backend.face_encodings(array, locations)
        return [
            _normalise(np.asarray(vector, dtype=np.float32)) for vector in found
        ], [tuple(location) for location in locations]

    def best(self, image_path):
        """Largest face, or None when there is no detectable face."""
        vectors, locations = self.embeddings(image_path)
        if not vectors:
            return None
        areas = [(right - left) * (bottom - top) for top, right, bottom, left in locations]
        return vectors[int(np.argmax(areas))]


def _open_rgb(image_path):
    from PIL import Image

    with Image.open(image_path) as image:
        return image.convert("RGB").copy()


def _normalise(vector):
    norm = float(np.linalg.norm(vector))
    return (vector / norm).tolist() if norm else vector.tolist()


def similarity(first, second):
    """Cosine similarity; both inputs are expected to be unit vectors."""
    left = np.asarray(first, dtype=np.float32)
    right = np.asarray(second, dtype=np.float32)
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0:
        return 0.0
    return float(np.dot(left, right) / denominator)


def person_cases():
    return [case for case in load_cases() if top_level_category(case) == "PERSON"]


def build_cache(model="hog", force=False):
    if CACHE.exists() and not force:
        payload = json.loads(CACHE.read_text())
        if payload.get("model") == model:
            return payload

    embedder = FaceEmbedder(model)
    records = {}
    for case in person_cases():
        try:
            vector = embedder.best(resolve_image(case))
        except Exception as exc:  # a corrupt image must not lose the whole run
            records[case["case_id"]] = {"status": "error", "detail": str(exc)[:120]}
            continue
        records[case["case_id"]] = (
            {"status": "ok", "embedding": vector} if vector
            else {"status": "no_face"}
        )

    payload = {
        "model": model,
        "detector": "face_recognition.face_encodings (dlib 128-d)",
        "cases": len(records),
        "with_face": sum(1 for r in records.values() if r["status"] == "ok"),
        "records": records,
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def load_cache(model="hog"):
    return build_cache(model=model)


def pairs_for_cache(records):
    """Positive = same entity; negative = different entity, both with a face."""
    from prepare_dataset import load_cases

    usable = sorted(cid for cid, rec in records.items() if rec["status"] == "ok")
    entity_of = {case["case_id"]: case["entity_id"] for case in load_cases()}
    positive, negative = [], []
    for i, left in enumerate(usable):
        for right in usable[i + 1 :]:
            pair = (left, right)
            target = positive if entity_of[left] == entity_of[right] else negative
            target.append(pair)
    return positive, negative


def vector_of(records, case_id):
    record = records.get(case_id, {})
    return record.get("embedding") if record.get("status") == "ok" else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--model", default="hog", choices=["hog", "cnn"])
    args = parser.parse_args()

    payload = build_cache(model=args.model, force=args.force)
    print(json.dumps({k: v for k, v in payload.items() if k != "records"}, indent=2))
    print(f"cache: {CACHE}")