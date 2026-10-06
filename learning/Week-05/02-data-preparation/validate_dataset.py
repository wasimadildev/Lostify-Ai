"""Fail loudly if the Week 05 dataset is not trustworthy.

Five checks, because each one has silently invalidated a real experiment:

1. schema        every required field present and of the right type
2. coverage      every case has an image on disk and a readable pixel size
3. taxonomy      category / top-level / subcategory agree with each other
4. leakage       no entity_id straddles two splits
5. labels        every pair label agrees with the entity_id ground truth

Exit code is non-zero when any check fails, so this can gate a pipeline run.

    python validate_dataset.py
    python validate_dataset.py --split test
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_dataset import (  # noqa: E402
    DATASET_DIR,
    PAIRS_PATH,
    REQUIRED_FIELDS,
    SPLIT_PATHS,
    TEST,
    entities,
    image_root,
    load_cases,
    load_pairs,
    load_split,
    resolve_image,
    subcategory,
    top_level_category,
)


class Report:
    def __init__(self):
        self.checks = {}
        self.failures = []

    def add(self, name, ok, detail=None):
        self.checks[name] = {"ok": ok, "detail": detail}
        if not ok:
            self.failures.append(name)
        return ok

    @property
    def ok(self):
        return not self.failures


def check_schema(cases, report):
    problems = []
    seen_ids = Counter()
    for case in cases:
        for field in REQUIRED_FIELDS:
            if field not in case or case[field] in (None, ""):
                problems.append(f"{case.get('case_id', '?')}: missing '{field}'")
        if case.get("case_id") in seen_ids:
            problems.append(f"duplicate case_id {case['case_id']}")
        seen_ids[case.get("case_id")] += 1
        if not str(case.get("description", "")).strip():
            problems.append(f"{case.get('case_id')}: blank description")
        if case.get("status") not in ("lost", "found"):
            problems.append(f"{case.get('case_id')}: bad status {case.get('status')}")
    return report.add("schema", not problems, problems or f"{len(cases)} cases valid")


def check_coverage(cases, report):
    from PIL import Image

    problems = []
    for case in cases:
        path = resolve_image(case)
        if not path.exists():
            problems.append(f"{case['case_id']}: missing {path}")
            continue
        try:
            with Image.open(path) as image:
                width, height = image.size
            if min(width, height) < 32:
                problems.append(f"{case['case_id']}: {width}x{height} too small")
        except OSError as exc:
            problems.append(f"{case['case_id']}: unreadable ({exc})")
    return report.add("coverage", not problems, problems or f"{len(cases)} images readable")


def check_taxonomy(cases, report):
    problems = []
    for case in cases:
        derived = top_level_category(case)
        if case.get("top_level") and case["top_level"] != derived:
            problems.append(
                f"{case['case_id']}: top_level '{case['top_level']}' != derived '{derived}'"
            )
        if case.get("subcategory") and case["subcategory"] != subcategory(case):
            problems.append(f"{case['case_id']}: subcategory disagrees with category")
    return report.add("taxonomy", not problems, problems or "all categories consistent")


def check_leakage(splits, report):
    problems = []
    owner = {}
    for name, cases in splits.items():
        for entity_id in entities(cases):
            if entity_id in owner and owner[entity_id] != name:
                problems.append(
                    f"entity {entity_id} appears in both {owner[entity_id]} and {name}"
                )
            owner[entity_id] = name
    detail = problems or (
        f"{len(owner)} entities, each confined to a single split "
        f"({dict(Counter(owner.values()))})"
    )
    return report.add("leakage", not problems, detail)


def check_pair_labels(pairs, report):
    problems = []
    ids = set()
    for pair in pairs:
        if pair["pair_id"] in ids:
            problems.append(f"duplicate pair_id {pair['pair_id']}")
        ids.add(pair["pair_id"])
        same_entity = pair["query_entity"] == pair["candidate_entity"]
        if same_entity != bool(pair["label"]):
            problems.append(
                f"{pair['pair_id']}: label {pair['label']} contradicts entities "
                f"({pair['query_entity']} vs {pair['candidate_entity']})"
            )
        if pair["query_case"] == pair["candidate_case"]:
            problems.append(f"{pair['pair_id']}: pairs a case with itself")
    positives = sum(1 for pair in pairs if pair["label"] == 1)
    negatives = len(pairs) - positives
    hard = sum(1 for pair in pairs if not pair["label"] and pair.get("hard_negative"))
    detail = problems or (
        f"{len(pairs)} pairs, {positives} positive, "
        f"{negatives} negative ({hard} of them same-class hard negatives)"
    )
    return report.add("pair_labels", not problems, detail)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="all",
                        choices=["all", "train", "validation", "test"])
    args = parser.parse_args()

    cases = load_cases()
    report = Report()

    check_schema(cases, report)
    check_coverage(cases, report)
    check_taxonomy(cases, report)

    names = list(SPLIT_PATHS) if args.split == "all" else [args.split]
    missing = [name for name in names if not SPLIT_PATHS[name].exists()]
    if missing:
        report.add("splits_present", False,
                   f"missing {missing}; run prepare_dataset.py --split")
    else:
        report.add("splits_present", True, f"found {', '.join(names)}")
        report.add("image_root", image_root().exists(), str(image_root()))
        check_leakage({name: load_split(name) for name in names}, report)

        if not PAIRS_PATH.exists():
            report.add("pair_labels", False,
                       f"{PAIRS_PATH} is missing; run prepare_dataset.py --pairs")
        else:
            check_pair_labels(load_pairs(), report)

    result = {
        "dataset_dir": str(DATASET_DIR),
        "cases": len(cases),
        "checks": report.checks,
        "failures": report.failures,
        "valid": report.ok,
    }
    for name, check in report.checks.items():
        print(f"[{'PASS' if check['ok'] else 'FAIL'}] {name}: {check['detail']}")
    print(f"\ndataset_valid={report.ok}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())