"""Week 05 YOLO stage: decide, export, then fine-tune.

The Week 05 README is explicit that fine-tuning is only worth it when the
evaluation shows a real domain gap *and* there is enough labelled data. So this
module refuses to fire a training run on roadmap-itis and makes the decision
first:

    python train.py --gap          # does the pretrained detector already work?
    python train.py --export       # build yolo_dataset/ (+ label provenance)
    python train.py --train        # fine-tune, only if the gate allows it

Label provenance
----------------
Real bounding boxes come from 01-dataset/annotations.json when that file exists.
The Week 04 corpus ships no boxes, so the default path *pseudo-labels* with the
pretrained detector and records `label_source: "pseudo"` in the export report.
Fine-tuning on your own predictions can at best preserve the teacher's
behaviour, which is exactly the trap the README warns about — hence the gate.

Outputs
-------
outputs/metrics/yolo_domain_gap.json     coverage of the pretrained detector
outputs/metrics/yolo_export.json         dataset build + label provenance
outputs/models/lostify-yolo/best.pt      fine-tuned checkpoint (when trained)
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

from prepare_dataset import (  # noqa: E402
    DATASET_DIR,
    METRICS_DIR,
    MODELS_DIR,
    TEST,
    TRAIN,
    VALIDATION,
    load_cases,
    load_split,
    resolve_image,
    top_level_category,
)

WEEK05 = Path(__file__).resolve().parent.parent
YOLO_DIR = WEEK05 / "03-yolo"
YOLO_DATASET = WEEK05 / "yolo_dataset"
ANNOTATIONS_PATH = DATASET_DIR / "annotations.json"
DATASET_YAML = YOLO_DIR / "dataset.yaml"
PRETRAINED_WEIGHTS = WEEK05.parent / "Week-04" / "yolo11n.pt"
FINETUNED_DIR = MODELS_DIR / "lostify-yolo"

CLASS_NAMES = ("phone", "wallet", "bag", "laptop")
MIN_DOMAIN_GAP = 0.60
MIN_BOXES_PER_CLASS = 25

# Lostify category -> the COCO classes a pretrained detector can already say.
COCO_EQUIVALENTS = {
    "smartphone": ("cell phone", "remote", "mouse"),
    "laptop": ("laptop", "tv", "keyboard"),
    "wallet": ("handbag", "suitcase", "backpack", "book"),
    "bag": ("backpack", "handbag", "suitcase", "handbag"),
    "luggage": ("suitcase", "backpack"),
    "backpack": ("backpack", "handbag"),
    "shopping bag": ("handbag", "suitcase"),
    "keys": (),
    "umbrella": ("umbrella",),
    "headphones": ("cell phone",),
    "water bottle": ("bottle", "cup", "wine glass"),
    "sunglasses": ("glasses",),
    "camera": ("cell phone", "camera"),
    "bicycle": ("bicycle",),
    "payphone": ("cell phone", "stop sign"),
}


def load_ultralytics():
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "ultralytics is required for the YOLO stage. "
            "Install ../Week-04/requirements-week04.txt."
        ) from exc
    return YOLO


def pretrained_weights():
    return str(PRETRAINED_WEIGHTS) if PRETRAINED_WEIGHTS.exists() else "yolo11n.pt"


def load_annotations():
    """Real boxes, if anyone has labelled the corpus."""
    if not ANNOTATIONS_PATH.exists():
        return {}
    payload = json.loads(ANNOTATIONS_PATH.read_text())
    return payload.get("annotations", payload)


# ----------------------------------------------------------------------------
# Day 4, step 0 — the domain gap
# ----------------------------------------------------------------------------
def domain_gap(weights=None, confidence=0.25):
    """How well does the COCO-pretrained detector already see Lostify objects?

    Returns per-category coverage plus a verdict. `coverage` is the share of
    item-like cases where the detector fires at least one box whose class maps
    to the case category. A high coverage on the classes that matter means
    fine-tuning has little headroom; a low coverage plus enough real boxes is
    the only situation where training is justified.
    """
    YOLO = load_ultralytics()
    model = YOLO(weights or pretrained_weights())

    cases = [case for case in load_cases() if top_level_category(case) in ("ITEM", "VEHICLE")]
    per_category = {}
    started = time.perf_counter()
    for case in cases:
        expected = COCO_EQUIVALENTS.get(str(case["category"]).lower(), ())
        result = model.predict(source=str(resolve_image(case)), conf=confidence, verbose=False)[0]
        detected = {result.names[int(cls)] for cls in result.boxes.cls.tolist()} if len(result.boxes) else set()
        hit = bool(detected & set(expected)) if expected else bool(detected)
        entry = per_category.setdefault(case["category"], {"cases": 0, "covered": 0, "classes_seen": set()})
        entry["cases"] += 1
        entry["covered"] += int(hit)
        entry["classes_seen"].update(detected & set(expected))
    elapsed = (time.perf_counter() - started) * 1000 / max(1, len(cases))

    summary = {
        category: {
            "cases": entry["cases"],
            "coverage": round(entry["covered"] / entry["cases"], 4),
            "coco_classes_hit": sorted(entry["classes_seen"]),
            "fine_tune_worthy": entry["cases"] >= 5 and
            (entry["covered"] / entry["cases"]) < 0.5,
        }
        for category, entry in sorted(per_category.items())
    }
    coverage = (
        sum(entry["covered"] for entry in per_category.values())
        / max(1, sum(entry["cases"] for entry in per_category.values()))
    )
    annotations = load_annotations()
    verdict = (
        "fine-tune" if coverage < MIN_DOMAIN_GAP and annotations
        else "keep pretrained"
    )
    report = {
        "weights": weights or pretrained_weights(),
        "item_like_cases": len(cases),
        "overall_coverage": round(coverage, 4),
        "threshold": MIN_DOMAIN_GAP,
        "real_annotations_available": len(annotations),
        "per_category": summary,
        "verdict": verdict,
        "reason": (
            f"pretrained coverage {coverage:.0%} "
            + ("below" if coverage < MIN_DOMAIN_GAP else "at or above")
            + f" the {MIN_DOMAIN_GAP:.0%} headroom threshold, with "
            + (f"{len(annotations)} annotated boxes"
               if annotations else "no annotated boxes available")
        ),
        "inference_ms_per_image": round(elapsed, 1),
    }
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (METRICS_DIR / "yolo_domain_gap.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


# ----------------------------------------------------------------------------
# Day 4, step 1 — export the YOLO dataset
# ----------------------------------------------------------------------------
def export_dataset(confidence=0.25, weights=None, force_pseudo=False):
    """Write images/{split} + labels/{split} in YOLO format.

    Boxes come from annotations.json when present, otherwise from the pretrained
    detector. Either way the provenance is written to yolo_export.json so no
    downstream reader can mistake pseudo-labels for ground truth.
    """
    YOLO = load_ultralytics()
    model = YOLO(weights or pretrained_weights())
    annotations = load_annotations()

    for split_dir in ("images", "labels"):
        shutil.rmtree(YOLO_DATASET / split_dir, ignore_errors=True)

    label_source = "annotations.json" if annotations and not force_pseudo else "pseudo"
    exported = {TRAIN: 0, VALIDATION: 0, TEST: 0}
    box_counts = {name: 0 for name in CLASS_NAMES}
    empty = []

    # The catalog calls the middle split "validation"; the YOLO convention (and
    # ultralytics' hardcoded expectation) is "val".
    for split, directory in ((TRAIN, "train"), (VALIDATION, "val"), (TEST, "test")):
        try:
            cases = load_split(split)
        except FileNotFoundError:
            continue
        image_dir = YOLO_DATASET / "images" / directory
        label_dir = YOLO_DATASET / "labels" / directory
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)

        for case in cases:
            source = resolve_image(case)
            target = image_dir / f"{case['case_id']}.jpg"
            shutil.copyfile(source, target)

            width, height = Image_size(source)
            boxes = annotations.get(case["case_id"], [])
            if not boxes:
                result = model.predict(source=str(source), conf=confidence, verbose=False)[0]
                boxes = [
                    {
                        "class": result.names[int(cls)],
                        "confidence": float(conf),
                        "bbox": [float(value) for value in box],
                    }
                    for box, conf, cls in zip(
                        result.boxes.xyxy.tolist(), result.boxes.conf.tolist(),
                        result.boxes.cls.tolist()
                    )
                ]

            lines = []
            for box in boxes:
                index = _lostify_class(box.get("class", ""))
                if index is None:
                    continue
                x1, y1, x2, y2 = box["bbox"]
                cx = ((x1 + x2) / 2) / width
                cy = ((y1 + y2) / 2) / height
                bw = (x2 - x1) / width
                bh = (y2 - y1) / height
                if bw <= 0 or bh <= 0:
                    continue
                lines.append(f"{index} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
                box_counts[CLASS_NAMES[index]] += 1
            (label_dir / f"{case['case_id']}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
            if not lines:
                empty.append(case["case_id"])
            exported[split] += 1

    report = {
        "dataset_dir": str(YOLO_DATASET),
        "config": str(DATASET_YAML),
        "classes": list(CLASS_NAMES),
        "label_source": label_source,
        "pseudo_label_warning": (
            "boxes were produced by the pretrained detector, so fine-tuning on "
            "them cannot exceed the teacher" if label_source == "pseudo" else None
        ),
        "exported": exported,
        "boxes_per_class": box_counts,
        "images_without_boxes": empty,
        "trainable": (
            label_source == "annotations.json"
            and min(box_counts.values(), default=0) >= MIN_BOXES_PER_CLASS
        ),
        "min_boxes_per_class": MIN_BOXES_PER_CLASS,
    }
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (METRICS_DIR / "yolo_export.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def Image_size(path):
    from PIL import Image

    with Image.open(path) as image:
        return image.size


def _lostify_class(name):
    """Map a detected COCO class name onto the four Lostify classes."""
    name = str(name).lower()
    if "cell phone" in name or "mobile" in name or "phone" in name or "remote" in name:
        return 0
    if "wallet" in name:
        return 1
    if any(token in name for token in ("bag", "backpack", "handbag", "suitcase")):
        return 2
    if "laptop" in name:
        return 3
    return None


# ----------------------------------------------------------------------------
# Day 4, step 2 — train
# ----------------------------------------------------------------------------
def train(epochs=20, imgsz=320, batch=8, weights=None, model_name="yolo11n"):
    """Fine-tune from the pretrained checkpoint, gate enforced."""
    gap = json.loads((METRICS_DIR / "yolo_domain_gap.json").read_text()) \
        if (METRICS_DIR / "yolo_domain_gap.json").exists() else domain_gap()
    if gap["verdict"] != "fine-tune":
        raise SystemExit(
            "Refusing to fine-tune.\n"
            f"  {gap['reason']}\n"
            "Week 05 rule: fine-tune only on a measured domain gap with real labels.\n"
            "Either annotate 01-dataset/annotations.json, or keep the pretrained\n"
            "detector and spend the effort on thresholding and re-ranking instead."
        )

    export = json.loads((METRICS_DIR / "yolo_export.json").read_text()) \
        if (METRICS_DIR / "yolo_export.json").exists() else export_dataset(weights=weights)
    if not export["trainable"]:
        raise SystemExit(
            f"Refusing to fine-tune: only {min(export['boxes_per_class'].values())} boxes "
            f"for the rarest class, below the {MIN_BOXES_PER_CLASS} needed."
        )

    YOLO = load_ultralytics()
    model = YOLO(weights or pretrained_weights())
    FINETUNED_DIR.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=str(FINETUNED_DIR),
        name="run",
        exist_ok=True,
        pretrained=True,
        verbose=False,
    )
    duration = time.perf_counter() - started
    best = FINETUNED_DIR / "run" / "weights" / "best.pt"
    return {
        "best_checkpoint": str(best) if best.exists() else None,
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "train_seconds": round(duration, 1),
        "log_dir": str(FINETUNED_DIR / "run"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap", action="store_true", help="Measure the domain gap only.")
    parser.add_argument("--export", action="store_true", help="Build yolo_dataset/.")
    parser.add_argument("--train", action="store_true", help="Fine-tune (gated).")
    parser.add_argument("--weights", default=None, help="Override the base checkpoint.")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--force-pseudo", action="store_true",
                        help="Pseudo-label even when annotations.json exists.")
    args = parser.parse_args()

    if not any((args.gap, args.export, args.train)):
        parser.error("choose at least one of --gap --export --train")

    if args.gap:
        report = domain_gap(args.weights, args.confidence)
        print(json.dumps({key: report[key] for key in (
            "overall_coverage", "verdict", "reason", "real_annotations_available")}, indent=2))
        for category, entry in report["per_category"].items():
            print(f"  {category:<15} coverage {entry['coverage']:.0%}"
                  f"  fine_tune_worthy={entry['fine_tune_worthy']}")
    if args.export:
        report = export_dataset(args.confidence, args.weights, args.force_pseudo)
        print(json.dumps(report, indent=2))
    if args.train:
        print(json.dumps(train(args.epochs, args.imgsz, args.batch, args.weights), indent=2))


if __name__ == "__main__":
    main()