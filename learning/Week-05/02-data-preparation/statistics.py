"""Report the state of the Week 05 dataset.

An experiment you cannot describe is an experiment you cannot defend, so this
prints (and persists) the numbers that go straight into the FYP: class balance,
split sizes, image resolutions, metadata completeness and duplication.

    python statistics.py
    python statistics.py --json outputs/metrics/dataset_statistics.json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_dataset import (  # noqa: E402
    CASES_PATH,
    DATASET_DIR,
    METRICS_DIR,
    PAIRS_PATH,
    SPLIT_PATHS,
    WEEK05,
    entities,
    hamming,
    load_cases,
    perceptual_fingerprint,
    resolve_image,
    subcategory,
    top_level_category,
)

RESOLUTION_BUCKETS = (
    ("<320", 0, 320),
    ("320-639", 320, 640),
    ("640-1023", 640, 1024),
    (">=1024", 1024, 10 ** 6),
)

METADATA_FIELDS = ("title", "description", "location", "latitude", "longitude",
                   "report_date", "category")


def _open(path):
    from PIL import Image

    with Image.open(path) as image:
        return image.convert("RGB")


def dimensions(cases):
    """Width/height for every case, from the image bytes on disk."""
    sizes = {}
    for case in cases:
        try:
            with _open(resolve_image(case)) as image:
                sizes[case["case_id"]] = image.size
        except OSError:
            sizes[case["case_id"]] = None
    return sizes


def bucket(width, height):
    side = min(width, height)
    for label, low, high in RESOLUTION_BUCKETS:
        if low <= side < high:
            return label
    return "unknown"


def duplicate_report(cases):
    """Mean-hash near-duplicates, so 'duplicates' is a number and not a claim."""
    hashes = {}
    for case in cases:
        try:
            hashes[case["case_id"]] = perceptual_fingerprint(resolve_image(case))
        except OSError:
            continue
    groups = defaultdict(list)
    ids = sorted(hashes)
    for position, left in enumerate(ids):
        for right in ids[position + 1:]:
            if hamming(hashes[left], hashes[right]) <= 4:
                groups[left].append(right)
    return {
        "method": "16x16 grayscale mean-hash, hamming <= 4",
        "groups": {key: value for key, value in groups.items() if value},
        "duplicate_images": sum(len(value) for value in groups.values()),
    }


def build(cases):
    sizes = dimensions(cases)
    widths = [width for width, _ in sizes.values() if width]
    heights = [height for _, height in sizes.values() if height]

    by_top = Counter(top_level_category(case) for case in cases)
    by_class = Counter(case["category"] for case in cases)
    by_type = Counter(case["type"] for case in cases)
    by_status = Counter(case["status"] for case in cases)
    by_location = Counter(case["location"] for case in cases)

    missing = defaultdict(list)
    for case in cases:
        for field in METADATA_FIELDS:
            if case.get(field) in (None, ""):
                missing[field].append(case["case_id"])

    resolved = [
        (case["case_id"], sizes[case["case_id"]])
        for case in cases if sizes.get(case["case_id"])
    ]

    return {
        "dataset_dir": str(DATASET_DIR),
        "catalog": str(CASES_PATH),
        "total_cases": len(cases),
        "total_entities": len(entities(cases)),
        "total_images": sum(1 for value in sizes.values() if value),
        "unreadable_images": sum(1 for value in sizes.values() if not value),
        "by_top_level_category": dict(by_top.most_common()),
        "by_category": dict(by_class.most_common()),
        "by_subcategory": dict(Counter(subcategory(case) for case in cases).most_common()),
        "by_case_type": dict(by_type.most_common()),
        "by_status": dict(by_status),
        "by_location": dict(by_location.most_common()),
        "resolution": {
            "average_width": round(sum(widths) / len(widths), 1) if widths else 0,
            "average_height": round(sum(heights) / len(heights), 1) if heights else 0,
            "minimum_side": min((min(w, h) for _, (w, h) in resolved), default=0),
            "maximum_side": max((min(w, h) for _, (w, h) in resolved), default=0),
            "buckets": dict(Counter(bucket(w, h) for _, (w, h) in resolved)),
        },
        "missing_metadata": {
            field: {"count": len(ids), "case_ids": ids[:10]}
            for field, ids in sorted(missing.items())
        },
        "metadata_completeness": round(
            1 - sum(len(ids) for ids in missing.values())
            / max(1, len(cases) * len(METADATA_FIELDS)), 4
        ),
        "splits": _split_summary(),
        "pairs": _pair_summary(),
        "duplicates": duplicate_report(cases),
        "class_balance": {
            "majority_class": by_class.most_common(1)[0][0] if by_class else None,
            "majority_class_share": round(
                by_class.most_common(1)[0][1] / max(1, len(cases)), 4
            ) if by_class else 0.0,
            "note": (
                "A 46-subject corpus is far too small for large-scale "
                "fine-tuning; results describe this dataset only."
            ),
        },
    }


def _split_summary():
    summary = {}
    for name, path in SPLIT_PATHS.items():
        if not path.exists():
            summary[name] = "missing"
            continue
        cases = json.loads(path.read_text())["cases"]
        summary[name] = {
            "cases": len(cases),
            "entities": len(entities(cases)),
            "share_of_cases": 0.0,
        }
    total = sum(entry["cases"] for entry in summary.values() if isinstance(entry, dict))
    for entry in summary.values():
        if isinstance(entry, dict) and total:
            entry["share_of_cases"] = round(entry["cases"] / total, 4)
    return summary


def _pair_summary():
    if not PAIRS_PATH.exists():
        return "missing"
    pairs = json.loads(PAIRS_PATH.read_text())["pairs"]
    return {
        "total": len(pairs),
        "positive": sum(1 for pair in pairs if pair["label"] == 1),
        "negative": sum(1 for pair in pairs if not pair["label"]),
        "same_class_negative": sum(
            1 for pair in pairs if not pair["label"] and pair.get("hard_negative")
        ),
        "by_split": dict(Counter(pair["split"] for pair in pairs)),
    }


def render(report):
    lines = [
        "Lostify AI - Week 05 dataset statistics",
        "=" * 52,
        f"Total cases      : {report['total_cases']}",
        f"Total entities   : {report['total_entities']}",
        f"Total images     : {report['total_images']}"
        + (f" ({report['unreadable_images']} unreadable)"
           if report["unreadable_images"] else ""),
        "",
        "By top-level category:",
    ]
    lines += [f"  {name:<12} {count:>4}"
              for name, count in report["by_top_level_category"].items()]
    lines += ["", "By category:"]
    lines += [f"  {name:<16} {count:>4}"
              for name, count in report["by_category"].items()]
    lines += ["", "By status: " + ", ".join(
        f"{name}={count}" for name, count in report["by_status"].items())]
    resolution = report["resolution"]
    lines += [
        "",
        "Resolution:",
        f"  average {resolution['average_width']}x{resolution['average_height']} px"
        f"  (shortest side {resolution['minimum_side']}-{resolution['maximum_side']} px)",
    ]
    lines += [f"  {name:<12} {count:>4} images"
              for name, count in resolution["buckets"].items()]

    lines += ["", "Splits:"]
    for name, entry in report["splits"].items():
        lines.append(f"  {name:<12} {entry}" if isinstance(entry, str) else
                     f"  {name:<12} {entry['cases']:>4} cases  "
                     f"{entry['entities']:>3} entities  "
                     f"{entry['share_of_cases'] * 100:>5.1f}%")

    pairs = report["pairs"]
    if isinstance(pairs, dict):
        lines += ["", "Pairs: " + ", ".join(f"{key}={value}"
                                           for key, value in pairs.items()
                                           if key != "by_split")]
    duplicates = report["duplicates"]
    lines += [
        "",
        f"Duplicate images : {duplicates['duplicate_images']} "
        f"({duplicates['method']})",
        f"Metadata complete: {report['metadata_completeness'] * 100:.1f}%",
    ]
    if report["missing_metadata"]:
        for field, entry in report["missing_metadata"].items():
            lines.append(f"  missing {field}: {entry['count']}")
    balance = report["class_balance"]
    lines += [
        "",
        f"Majority class   : {balance['majority_class']} "
        f"({balance['majority_share'] * 100:.1f}% of cases)"
        if "majority_share" in balance else
        f"Majority class   : {balance['majority_class']}",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=METRICS_DIR / "dataset_statistics.json")
    args = parser.parse_args()

    report = build(load_cases())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n")
    print(render(report))
    print(f"\nWritten to {args.json.relative_to(WEEK05) if WEEK05 in args.json.parents else args.json}")


if __name__ == "__main__":
    main()