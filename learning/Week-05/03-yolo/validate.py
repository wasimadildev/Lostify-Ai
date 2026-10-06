"""Pretrained vs fine-tuned YOLO, measured on the Week 05 validation split.

    python validate.py                     # both arms, if a checkpoint exists
    python validate.py --only pretrained
    python validate.py --only finetuned

Writes outputs/metrics/yolo_comparison.json. When no fine-tuned checkpoint
exists the comparison is still produced for the pretrained arm, with
`finetuned: null` and a reason, because "we did not fine-tune, and here is the
measurement that justified stopping" is a stronger result than a fabricated one.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

from prepare_dataset import METRICS_DIR, VALIDATION, load_split, resolve_image  # noqa: E402

WEEK05 = Path(__file__).resolve().parent.parent
DATASET_YAML = Path(__file__).resolve().parent / "dataset.yaml"
FINETUNED = WEEK05 / "outputs" / "models" / "lostify-yolo" / "run" / "weights" / "best.pt"
COMPARISON = METRICS_DIR / "yolo_comparison.json"


def measure(weights, split=VALIDATION, imgsz=320):
    """Precision / recall / mAP / latency for one checkpoint on one split."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit("ultralytics is required. See requirements-week05.txt.") from exc

    try:
        cases = load_split(split)
    except FileNotFoundError:
        return {"available": False, "reason": f"{split}.json missing; run prepare_dataset.py"}

    if not cases:
        return {"available": False, "reason": f"{split} split is empty"}

    model = YOLO(weights)
    model.predict(source=str(resolve_image(cases[0])), imgsz=imgsz, verbose=False)  # warm up
    timed = []
    for case in cases:
        clock = time.perf_counter()
        model.predict(source=str(resolve_image(case)), imgsz=imgsz, verbose=False)
        timed.append((time.perf_counter() - clock) * 1000)

    metrics = {
        "available": True,
        "weights": str(weights),
        "images": len(cases),
        "inference_ms": round(median(timed), 1) if timed else None,
        "inference_ms_min": round(min(timed), 1) if timed else None,
    }

    directory = {"train": "train", "validation": "val", "test": "test"}[split]
    labelled = _label_coverage(split, directory)
    metrics["labelled_images"] = labelled["images_with_boxes"]
    metrics["label_source"] = labelled["label_source"]
    if not labelled["images_with_boxes"]:
        metrics.update({
            "precision": None, "recall": None, "map50": None, "map50_95": None,
            "available": False,
            "reason": (
                f"no ground-truth boxes in the {split} split: mAP, precision and "
                "recall are undefined without human labels. Latency is still "
                "measured. See 03-yolo/README.md for how to add annotations."
            ),
        })
        return metrics

    started = time.perf_counter()
    results = model.val(
        data=str(DATASET_YAML),
        split="val",
        imgsz=imgsz,
        verbose=False,
        plots=False,
    )
    metrics["validation_ms"] = round((time.perf_counter() - started) * 1000, 1)
    metrics["precision"] = round(float(results.box.mp), 4)
    metrics["recall"] = round(float(results.box.mr), 4)
    metrics["map50"] = round(float(results.box.map50), 4)
    metrics["map50_95"] = round(float(results.box.map), 4)
    if hasattr(results.box, "maps") and len(results.box.maps):
        metrics["map50_95_per_class"] = {
            name: round(float(value), 4)
            for name, value in zip(results.names.values(), results.box.maps)
        }
    return metrics


def _label_coverage(split, directory):
    """How many images in this split actually carry a box, and where it came from."""
    labels = WEEK05 / "yolo_dataset" / "labels" / directory
    with_boxes = sum(1 for path in labels.glob("*.txt") if path.read_text().strip()) \
        if labels.exists() else 0
    report = METRICS_DIR / "yolo_export.json"
    source = "unknown"
    if report.exists():
        source = json.loads(report.read_text()).get("label_source", "unknown")
    return {"images_with_boxes": with_boxes, "label_source": source}


def compare(imgsz=320):
    from train import pretrained_weights

    arms = {"pretrained": pretrained_weights()}
    if FINETUNED.exists():
        arms["finetuned"] = str(FINETUNED)

    result = {
        "split": VALIDATION,
        "config": str(DATASET_YAML),
        "arms": {name: measure(weights, imgsz=imgsz) for name, weights in arms.items()},
        "decision": None,
        "reason": None,
    }

    pre = result["arms"]["pretrained"]
    fine = result["arms"].get("finetuned")
    if fine and fine.get("available"):
        delta_map = round(fine["map50_95"] - pre["map50_95"], 4)
        delta_ms = round(fine["inference_ms"] - pre["inference_ms"], 1)
        improved = delta_map > 0
        result["decision"] = "adopt fine-tuned" if improved else "keep pretrained"
        result["reason"] = (
            f"mAP50-95 {pre['map50_95']} -> {fine['map50_95']} ({delta_map:+}), "
            f"latency {delta_ms:+} ms"
        )
    else:
        result["decision"] = "keep pretrained"
        result["reason"] = (
            "no fine-tuned checkpoint; see yolo_domain_gap.json for the "
            "measurement that justified not training one"
        )

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON.write_text(json.dumps(result, indent=2) + "\n")
    return result


def render(result):
    lines = [f"YOLO comparison ({result['split']} split)", "-" * 62]
    lines += [f"{'arm':<12}{'P':>9}{'R':>9}{'mAP50':>9}{'mAP50-95':>11}{'ms':>9}"]
    lines += ["-" * 62]
    for name, arm in result["arms"].items():
        latency = f"{arm['inference_ms']:>9.1f}" if arm.get("inference_ms") else f"{'n/a':>9}"
        cells = [
            f"{value:>9.3f}" if value is not None else f"{'n/a':>9}"
            for value in (arm.get("precision"), arm.get("recall"), arm.get("map50"))
        ]
        map95 = f"{arm['map50_95']:>11.3f}" if arm.get("map50_95") is not None else f"{'n/a':>11}"
        lines.append(f"{name:<12}{''.join(cells)}{map95}{latency}")
        if arm.get("reason"):
            lines.append(f"  ↳ {arm['reason']}")
    lines += ["-" * 62, f"decision: {result['decision']}", f"reason  : {result['reason']}"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["pretrained", "finetuned", "both"], default="both")
    parser.add_argument("--imgsz", type=int, default=320)
    args = parser.parse_args()

    if args.only == "both":
        result = compare(args.imgsz)
    else:
        from train import pretrained_weights

        weights = pretrained_weights() if args.only == "pretrained" else str(FINETUNED)
        if args.only == "finetuned" and not FINETUNED.exists():
            raise SystemExit(f"No checkpoint at {FINETUNED}. Run train.py --train first.")
        result = {
            "split": VALIDATION,
            "config": str(DATASET_YAML),
            "arms": {args.only: measure(weights, imgsz=args.imgsz)},
            "decision": None,
            "reason": "single arm requested",
        }
    print(render(result))


if __name__ == "__main__":
    main()