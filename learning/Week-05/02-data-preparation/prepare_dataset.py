"""Turn the Week 05 case catalog into train / validation / test splits and pairs.

This module is the dataset API for the whole week. Every other Week 05 stage
(03-yolo, 04-clip, 05-face, 06-ranking, 07-evaluation) imports the path helpers
and the case loaders from here, so there is exactly one place that knows how a
case is laid out on disk.

Run order:

    python prepare_dataset.py --materialize --clean --split --pairs

Pipeline stages
---------------
materialize  Render the "found" view of every entity so the matching index has
             a genuinely different image for each lost report.
clean        Drop corrupted, duplicated, undersized and mislabelled cases.
split        Group-aware 70/15/15 split. Images of the same entity never cross
             a split boundary, which is what prevents data leakage.
pairs        Build positive (same entity) and negative (different entity) pairs
             used by CLIP contrastive training and by the ranker.
"""

import argparse
import json
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

WEEK05 = Path(__file__).resolve().parent.parent
DATASET_DIR = WEEK05 / "01-dataset"
IMAGES_DIR = DATASET_DIR / "images"
FOUND_DIR = IMAGES_DIR / "found"
OUTPUTS_DIR = WEEK05 / "outputs"
METRICS_DIR = OUTPUTS_DIR / "metrics"
MODELS_DIR = OUTPUTS_DIR / "models"
GRAPHS_DIR = OUTPUTS_DIR / "graphs"

CASES_PATH = DATASET_DIR / "cases.json"
SPLIT_PATHS = {
    "train": DATASET_DIR / "train.json",
    "validation": DATASET_DIR / "validation.json",
    "test": DATASET_DIR / "test.json",
}
PAIRS_PATH = DATASET_DIR / "pairs.json"

TRAIN, VALIDATION, TEST = "train", "validation", "test"

SPLIT_RATIOS = {TRAIN: 0.70, VALIDATION: 0.15, TEST: 0.15}

MIN_SIDE = 160
MIN_FILE_BYTES = 2048

TOP_LEVEL_CATEGORIES = ("PERSON", "PET", "ITEM", "VEHICLE", "DOCUMENT", "OTHER")

SUBCATEGORIES = {
    "PET": ("dog", "cat", "bird", "rabbit", "other"),
    "ITEM": ("mobile", "laptop", "bag", "wallet", "watch", "keys", "bicycle", "other"),
    "VEHICLE": ("car", "motorcycle", "bicycle", "other"),
}

CATEGORY_MAP = {
    "cat": ("PET", "cat"),
    "dog": ("PET", "dog"),
    "person": ("PERSON", "person"),
    "smartphone": ("ITEM", "mobile"),
    "laptop": ("ITEM", "laptop"),
    "bag": ("ITEM", "bag"),
    "backpack": ("ITEM", "bag"),
    "luggage": ("ITEM", "bag"),
    "shopping bag": ("ITEM", "bag"),
    "wallet": ("ITEM", "wallet"),
    "keys": ("ITEM", "keys"),
    "watch": ("ITEM", "watch"),
    "payphone": ("OTHER", "payphone"),
    "umbrella": ("ITEM", "other"),
    "headphones": ("ITEM", "other"),
    "water bottle": ("ITEM", "other"),
    "sunglasses": ("ITEM", "other"),
    "camera": ("ITEM", "other"),
    "bicycle": ("VEHICLE", "bicycle"),
    "car": ("VEHICLE", "car"),
    "motorcycle": ("VEHICLE", "motorcycle"),
    "document": ("DOCUMENT", "other"),
}

REQUIRED_FIELDS = (
    "case_id", "type", "category", "image", "description",
    "location", "status", "entity_id", "report_date",
)


def load_catalog():
    """Return the raw cases.json document."""
    if not CASES_PATH.exists():
        raise FileNotFoundError(
            f"{CASES_PATH} is missing. Restore the Week 05 case catalog first."
        )
    return json.loads(CASES_PATH.read_text())


def load_cases():
    """Return the catalog as a list of case dicts."""
    return load_catalog()["cases"]


def save_catalog(catalog):
    CASES_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")


def image_root():
    """Resolve the directory that plain `source` images live in."""
    return (DATASET_DIR / load_catalog()["image_root"]).resolve()


def resolve_image(case):
    """Absolute path of the image a case points at."""
    return (DATASET_DIR / case["image"]).resolve()


def is_found(case):
    """True for a found report, whatever its category.

    `type` has six values (`found_item`, `found_pet`, `found_person` and their
    `lost_` counterparts), so `type == "found_item"` silently misses two thirds
    of the found corpus. `status` is the only field that is `found`/`lost` for
    every case, so every downstream stage must ask this instead.
    """
    return str(case.get("status", "")).lower() == "found"


def top_level_category(case):
    return CATEGORY_MAP.get(str(case["category"]).lower(), ("OTHER", "other"))[0]


def subcategory(case):
    return CATEGORY_MAP.get(str(case["category"]).lower(), ("OTHER", "other"))[1]


def entities(cases):
    """Group cases by entity id: {entity_id: [case, ...]}."""
    grouped = defaultdict(list)
    for case in cases:
        grouped[case["entity_id"]].append(case)
    return dict(grouped)


def build_augmented_view(case, seed):
    """Render a second, different photograph of the same real-world entity.

    The source corpus holds exactly one photo per subject, so a lost report and
    a found report of the same entity cannot come from two different files. The
    found report is therefore rendered from the same source photo under a
    deterministic viewpoint + photometry recipe: the subject is identical (the
    label is exact), while framing, scale and lighting differ the way a second
    person's phone photo would.

    Deterministic in `seed`, so the dataset is reproducible.
    """
    rng = random.Random(f"{case['entity_id']}:{seed}")
    with Image.open(resolve_image(case)) as original:
        image = original.convert("RGB")
        width, height = image.size

        zoom = rng.uniform(0.72, 0.88)
        crop_width = max(MIN_SIDE, int(width * zoom))
        crop_height = max(MIN_SIDE, int(height * zoom))
        left = rng.randint(0, max(0, width - crop_width))
        top = rng.randint(0, max(0, height - crop_height))
        view = image.crop((left, top, left + crop_width, top + crop_height))

        view = view.resize(
            (rng.randint(288, 448), rng.randint(288, 448)), Image.LANCZOS
        )
        if rng.random() < 0.5:
            view = view.transpose(Image.FLIP_LEFT_RIGHT)
        view = view.rotate(rng.uniform(-14, 14), resample=Image.BICUBIC, expand=False)

        view = ImageEnhance.Brightness(view).enhance(rng.uniform(0.82, 1.18))
        view = ImageEnhance.Contrast(view).enhance(rng.uniform(0.85, 1.15))
        view = ImageEnhance.Color(view).enhance(rng.uniform(0.85, 1.15))
        if rng.random() < 0.35:
            view = view.filter(ImageFilter.GaussianBlur(0.6))

        FOUND_DIR.mkdir(parents=True, exist_ok=True)
        target = FOUND_DIR / f"{case['case_id']}.jpg"
        view.save(target, "JPEG", quality=92)
    return target


def _shift_location(case, catalog):
    """Move a found report to a nearby-but-different place and date."""
    locations = catalog.get("locations", {})
    name = case["location"]
    nearby = locations.get(name, {}).get("nearby", [])
    target = random.Random(case["entity_id"]).choice(nearby) if nearby else name
    coords = locations.get(target, {}).get("latlon", [None, None])
    reported = date.fromisoformat(case["report_date"]) + timedelta(
        days=random.Random(case["entity_id"] + "d").randint(2, 9)
    )
    return target, coords[0], coords[1], reported.isoformat()


def materialize_views(catalog, seed=20260905):
    """Render and register the found report for every lost report."""
    cases = {case["case_id"]: case for case in catalog["cases"]}
    entities_by_id = entities(catalog["cases"])
    made = 0
    for entity_id, group in entities_by_id.items():
        lost = [case for case in group if case["status"] == "lost"]
        if not lost:
            continue
        if any(case["status"] == "found" for case in group):
            continue
        source = sorted(lost, key=lambda case: case["case_id"])[0]
        target_path = build_augmented_view(source, seed)
        location, latitude, longitude, reported = _shift_location(source, catalog)
        found_id = f"FOUND-{source['case_id']}"
        cases[found_id] = {
            "case_id": found_id,
            "entity_id": entity_id,
            "type": source["type"].replace("lost_", "found_"),
            "category": source["category"],
            "title": f"Found: {source['title']}",
            "description": f"Found item reported matching: {source['description']}",
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "status": "found",
            "report_date": reported,
            "image": str(target_path.relative_to(DATASET_DIR)),
            "image_origin": source["case_id"],
            "view_recipe": "crop+resize+flip+rotate+brightness+contrast+color",
            "split": None,
        }
        made += 1
    catalog["cases"] = sorted(cases.values(), key=lambda case: case["case_id"])
    catalog["entities"] = len(entities_by_id)
    save_catalog(catalog)
    return made


def perceptual_fingerprint(path):
    """Cheap duplicate detector: 16x16 grayscale mean-hash of the pixels."""
    with Image.open(path) as image:
        small = image.convert("L").resize((16, 16), Image.BILINEAR)
        pixels = list(small.tobytes())
    average = sum(pixels) / len(pixels)
    bits = 0
    for pixel in pixels:
        bits = (bits << 1) | int(pixel > average)
    return f"{bits:064x}"


def hamming(left, right):
    return bin(int(left, 16) ^ int(right, 16)).count("1")


def clean_cases(cases, report):
    """Remove corrupted, duplicated, undersized and mislabelled cases."""
    kept, dropped = [], []
    fingerprints = {}
    for case in cases:
        path = resolve_image(case)
        reason = None
        if not path.exists():
            reason = "missing_image"
        elif path.stat().st_size < MIN_FILE_BYTES:
            reason = "file_too_small"
        else:
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    image = image.convert("RGB")
                    width, height = image.size
                if min(width, height) < MIN_SIDE:
                    reason = "resolution_too_low"
                else:
                    case = {**case, "width": width, "height": height}
                    fingerprint = perceptual_fingerprint(path)
                    for seen_id, seen_hash in fingerprints.items():
                        if hamming(fingerprint, seen_hash) <= 4:
                            reason = f"duplicate_of:{seen_id}"
                            break
                    fingerprints[case["case_id"]] = fingerprint
            except OSError:
                reason = "corrupted_image"
        if reason:
            dropped.append({"case_id": case["case_id"], "reason": reason})
        else:
            kept.append(case)
    report["cleaning"] = {
        "kept": len(kept),
        "dropped": len(dropped),
        "dropped_detail": dropped,
        "rules": {
            "min_side": MIN_SIDE,
            "min_file_bytes": MIN_FILE_BYTES,
            "max_mean_hash_distance": 4,
        },
    }
    return kept


def validate_labels(cases, report):
    """Flag cases whose taxonomy or status fields contradict the catalog."""
    problems = []
    for case in cases:
        top_level = top_level_category(case)
        sub = subcategory(case)
        allowed = SUBCATEGORIES.get(top_level)
        if allowed and sub not in allowed:
            problems.append(f"{case['case_id']}: subcategory '{sub}' invalid for {top_level}")
        if case["status"] not in ("lost", "found"):
            problems.append(f"{case['case_id']}: invalid status '{case['status']}'")
        if not str(case["description"]).strip():
            problems.append(f"{case['case_id']}: empty description")
    report["labels"] = {"checked": len(cases), "problems": problems}
    return problems


def group_split(cases, seed=42):
    """Group-aware 70/15/15 split keyed on entity_id (no leakage)."""
    grouped = entities(cases)
    order = sorted(grouped)
    random.Random(seed).shuffle(order)

    total = len(order)
    train_cut = max(1, round(total * SPLIT_RATIOS[TRAIN]))
    validation_cut = max(1, round(total * SPLIT_RATIOS[VALIDATION]))
    if train_cut + validation_cut >= total:
        train_cut = max(1, total - 2)

    assignment = {}
    for position, entity_id in enumerate(order):
        if position < train_cut:
            assignment[entity_id] = TRAIN
        elif position < train_cut + validation_cut:
            assignment[entity_id] = VALIDATION
        else:
            assignment[entity_id] = TEST

    splits = {TRAIN: [], VALIDATION: [], TEST: []}
    for case in cases:
        case = {**case, "split": assignment[case["entity_id"]]}
        splits[case["split"]].append(case)
    for name in splits:
        splits[name].sort(key=lambda case: case["case_id"])
    return splits, assignment


def build_pairs(splits, max_positives_per_entity=3, negatives_per_positive=2, seed=7):
    """Positive pairs share an entity; negative pairs never do.

    Positives are the lost -> found pair of one entity, which is exactly the
    relationship Lostify has to get right. Negatives are drawn inside the same
    split so the model cannot separate them by split membership, and half of
    them are forced to share the top-level category so the model cannot win by
    category filtering alone.
    """
    rng = random.Random(seed)
    pairs = []
    for split_name, cases in splits.items():
        by_entity = entities(cases)

        positives = []
        for entity_id, group in sorted(by_entity.items()):
            lost = [case for case in group if case["status"] == "lost"]
            found = [case for case in group if case["status"] == "found"]
            for query in lost:
                for candidate in found:
                    positives.append((query, candidate, entity_id))
        rng.shuffle(positives)

        capped, seen = [], Counter()
        for query, candidate, entity_id in positives:
            if seen[entity_id] >= max_positives_per_entity:
                continue
            seen[entity_id] += 1
            capped.append((query, candidate))

        queries = [query for query, _ in capped] or [
            case for case in cases if case["status"] == "lost"
        ]
        candidates = [case for case in cases if case["status"] == "found"]
        wanted = len(capped) * negatives_per_positive
        hard = max(1, wanted // 2)

        negatives = []
        used = {(query["case_id"], candidate["case_id"]) for query, candidate in capped}
        guard = 0
        while len(negatives) < wanted and guard < wanted * 80:
            guard += 1
            query = rng.choice(queries)
            candidate = rng.choice(candidates)
            if candidate["case_id"] == query["case_id"]:
                continue
            if candidate["entity_id"] == query["entity_id"]:
                continue
            key = (query["case_id"], candidate["case_id"])
            if key in used:
                continue
            same_class = top_level_category(candidate) == top_level_category(query)
            if (len(negatives) < hard) != same_class:
                continue
            used.add(key)
            negatives.append((query, candidate))

        for group, label in ((capped, 1), (negatives, 0)):
            for query, candidate in group:
                pairs.append({
                    "pair_id": f"{split_name[:3].upper()}-{label}-"
                               f"{query['case_id']}-{candidate['case_id']}",
                    "split": split_name,
                    "query_case": query["case_id"],
                    "candidate_case": candidate["case_id"],
                    "query_entity": query["entity_id"],
                    "candidate_entity": candidate["entity_id"],
                    "query_class": top_level_category(query),
                    "candidate_class": top_level_category(candidate),
                    # Hard = a negative that shares the top-level category, so the
                    # model cannot win by category filtering alone. A positive
                    # pair is never "hard", even though its classes match.
                    "hard_negative": bool(
                        label == 0
                        and top_level_category(candidate) == top_level_category(query)
                    ),
                    "query_image": query["image"],
                    "candidate_image": candidate["image"],
                    "label": label,
                })
    pairs.sort(key=lambda pair: pair["pair_id"])
    return pairs


def write_splits(splits, report, pairs=None):
    for name, cases in splits.items():
        SPLIT_PATHS[name].write_text(json.dumps({
            "split": name,
            "generated_by": "prepare_dataset.py",
            "protocol": "grouped by entity_id to prevent leakage",
            "cases": cases,
        }, indent=2, ensure_ascii=False) + "\n")

    report["splits"] = {
        name: {
            "cases": len(cases),
            "entities": len(entities(cases)),
            "lost": sum(1 for case in cases if case["status"] == "lost"),
            "found": sum(1 for case in cases if case["status"] == "found"),
        }
        for name, cases in splits.items()
    }

    if pairs is None:
        return report

    PAIRS_PATH.write_text(json.dumps({
        "protocol": "positive = same entity_id, negative = different entity_id",
        "counts": dict(Counter(pair["label"] for pair in pairs)),
        "pairs": pairs,
    }, indent=2, ensure_ascii=False) + "\n")
    report["pairs"] = dict(Counter(pair["label"] for pair in pairs))
    return report


def load_split(name):
    path = SPLIT_PATHS.get(name, DATASET_DIR / f"{name}.json")
    if not path.exists():
        raise FileNotFoundError(f"Split file {path} is missing. Run prepare_dataset.py first.")
    return json.loads(path.read_text())["cases"]


def load_pairs():
    if not PAIRS_PATH.exists():
        raise FileNotFoundError(f"{PAIRS_PATH} is missing. Run prepare_dataset.py first.")
    return json.loads(PAIRS_PATH.read_text())["pairs"]


def load_report():
    path = METRICS_DIR / "dataset_build.json"
    return json.loads(path.read_text()) if path.exists() else {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true",
                        help="Render the found view of every entity.")
    parser.add_argument("--clean", action="store_true",
                        help="Drop corrupted, duplicated and undersized cases.")
    parser.add_argument("--split", action="store_true",
                        help="Write group-aware train/validation/test.json files.")
    parser.add_argument("--pairs", action="store_true",
                        help="Write positive/negative pairs.json for contrastive training.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stages = [args.materialize, args.clean, args.split, args.pairs]
    if not any(stages):
        parser.error("choose at least one of --materialize --clean --split --pairs")

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    cases = catalog["cases"]
    report = {"stages": [name for name, flag in (
        ("materialize", args.materialize), ("clean", args.clean),
        ("split", args.split), ("pairs", args.pairs)) if flag]}

    if args.materialize:
        report["materialized_found_reports"] = materialize_views(catalog)
        cases = catalog["cases"]

    if args.clean:
        cases = clean_cases(cases, report)
        validate_labels(cases, report)

    if args.split or args.pairs:
        splits, assignment = group_split(cases, seed=args.seed)
        catalog["cases"] = sorted(
            ({**case, "split": assignment[case["entity_id"]]} for case in cases),
            key=lambda case: case["case_id"],
        )
        save_catalog(catalog)
        report = write_splits(
            splits,
            report,
            build_pairs(splits) if args.pairs else None,
        )

    (METRICS_DIR / "dataset_build.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()