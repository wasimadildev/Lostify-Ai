"""Turn YOLO detections into the object evidence the ranker consumes.

The re-ranking engine in 06-ranking needs a single comparable number per
candidate, not a box list. `object_score` here is the Jaccard overlap between the
query's detected class multiset and the candidate's, so "phone vs phone in a
hand" and "phone vs phone on a table" score differently.

    python inference.py PETS-01
    python inference.py --self-pair FOUND-PETS-01 PETS-01
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

from prepare_dataset import load_cases, resolve_image  # noqa: E402


class ObjectExtractor:
    """Cached YOLO detector that reports detections and object features."""

    def __init__(self, weights=None, confidence=0.25, min_objects=False):
        try:
            from ultralytics import YOLO
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "YOLO requires ultralytics. See requirements-week05.txt."
            ) from exc
        from train import pretrained_weights

        self.confidence = confidence
        self.min_objects = min_objects
        self.model = YOLO(str(weights) if weights else pretrained_weights())
        self._cache = {}
        self._pinned = {}

    def detect(self, image):
        """Detections for a PIL image or a path. Cached by input identity."""
        if not isinstance(image, (str, Path)):
            try:
                from PIL import Image as PILImage
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise RuntimeError("Pillow is required to load image arrays.") from exc
            if not isinstance(image, PILImage.Image):
                raise TypeError(
                    "pass a path or a PIL Image, not "
                    f"{type(image).__name__}. Use prepare_dataset.resolve_image(case)."
                )
        key = id(image) if not isinstance(image, (str, Path)) else str(image)
        if key not in self._cache:
            source = str(image) if isinstance(image, (str, Path)) else image
            result = self.model.predict(
                source=source, conf=self.confidence, verbose=False
            )[0]
            self._cache[key] = [
                {
                    "class": result.names[int(cls)],
                    "confidence": round(float(conf), 4),
                    "bbox": [round(float(value), 1) for value in box],
                }
                for box, conf, cls in zip(
                    result.boxes.xyxy.tolist(),
                    result.boxes.conf.tolist(),
                    result.boxes.cls.tolist(),
                )
            ]
            # Keep in-memory images alive: id() is reused after collection, and a
            # recycled id would hand back another image's detections.
            if not isinstance(image, (str, Path)):
                self._pinned[key] = image
        return self._cache[key]

    def classes(self, image):
        return [detection["class"] for detection in self.detect(image)]

    def bag(self, image):
        """Multiset of detected classes, for set comparison."""
        return Counter(self.classes(image))


def jaccard(query_bag, candidate_bag):
    """Class-set similarity in [0, 1]. Two empty detections score 0, not 1."""
    left, right = set(query_bag), set(candidate_bag)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def object_score(extractor, query_image, candidate_image):
    """Object evidence for one (query, candidate) pair."""
    query_bag = extractor.bag(query_image)
    candidate_bag = extractor.bag(candidate_image)
    score = jaccard(query_bag, candidate_bag)
    return {
        "object_score": round(score, 4),
        "query_objects": dict(query_bag),
        "candidate_objects": dict(candidate_bag),
        "shared_objects": sorted(set(query_bag) & set(candidate_bag)),
    }


def score_case_pairs(extractor, query_case, candidates):
    """Vectorised convenience wrapper used by the ranking feature builder."""
    query_bag = extractor.bag(resolve_image(query_case))
    rows = []
    for candidate in candidates:
        candidate_bag = extractor.bag(resolve_image(candidate))
        rows.append({
            "case_id": candidate["case_id"],
            "object_score": round(jaccard(query_bag, candidate_bag), 4),
            "candidate_objects": dict(candidate_bag),
        })
    return rows


def _case(case_id):
    for case in load_cases():
        if case["case_id"] == case_id:
            return case
    raise SystemExit(f"Unknown case id '{case_id}'. See 01-dataset/cases.json.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", help="case id or image path")
    parser.add_argument("--against", help="second case id to score against")
    parser.add_argument("--weights", default=None)
    parser.add_argument("--confidence", type=float, default=0.25)
    args = parser.parse_args()

    extractor = ObjectExtractor(weights=args.weights, confidence=args.confidence)
    first = _case(args.case) if not Path(args.case).exists() else None
    image = resolve_image(first) if first else args.case

    detections = extractor.detect(image)
    print(json.dumps({"image": str(image), "detections": detections}, indent=2))

    if args.against:
        second = _case(args.against)
        if first:
            evidence = object_score(extractor, image, resolve_image(second))
        else:
            left, right = extractor.bag(image), extractor.bag(resolve_image(second))
            evidence = {
                "object_score": round(jaccard(left, right), 4),
                "query_objects": dict(left),
                "candidate_objects": dict(right),
                "shared_objects": sorted(set(left) & set(right)),
            }
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()