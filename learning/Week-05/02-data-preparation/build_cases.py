"""One-off builder: 01-dataset/cases.json from the Week 04 corpus.

Kept out of the Week 05 pipeline on purpose. cases.json is committed *data*;
this script only documents exactly how it was derived from the 46 curated
Week 04 photographs, so the catalog can be regenerated or audited later.

    python 02-data-preparation/build_cases.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_dataset import DATASET_DIR, CASES_PATH, CATEGORY_MAP  # noqa: E402

WEEK04 = DATASET_DIR.parent.parent / "Week-04"
SOURCE_METADATA = WEEK04 / "metadata.json"
SOURCE_CATALOG = WEEK04 / "catalog.json"

STATUS = "lost"
SPLIT_FIELD = None


def load_locations():
    catalog = json.loads(SOURCE_CATALOG.read_text())
    latlon = catalog.get("locations", {})
    return {
        name: {"latlon": coords, "nearby": []}
        for name, coords in latlon.items()
    }


def build_nearby(locations):
    """Give each city a few plausible neighbours so found reports can move."""
    ordered = sorted(locations)
    for position, name in enumerate(ordered):
        neighbours = [ordered[(position + step) % len(ordered)] for step in (1, 2)]
        locations[name]["nearby"] = neighbours
    return locations


def main():
    metadata = json.loads(SOURCE_METADATA.read_text())
    locations = build_nearby(load_locations())

    cases = []
    for case_id, record in sorted(metadata.items()):
        category = str(record["category"]).lower()
        top_level, sub = CATEGORY_MAP.get(category, ("OTHER", "other"))
        cases.append({
            "case_id": case_id,
            "entity_id": f"ENT-{case_id}",
            "type": record["case_type"],
            "category": category,
            "top_level": top_level,
            "subcategory": sub,
            "title": record["title"],
            "description": record["description"],
            "location": record["location"],
            "latitude": record.get("latitude"),
            "longitude": record.get("longitude"),
            "status": STATUS,
            "report_date": record["date_lost"],
            "image": f"../../Week-04/{record['image_path']}",
            "image_origin": record["image_path"],
            "split": SPLIT_FIELD,
        })

    catalog = {
        "version": "1.0",
        "description": (
            "Lostify AI Week 05 case catalog. 46 curated reports over 46 real "
            "subjects, inherited from the Week 04 corpus. Each entity receives a "
            "matched 'found' report during materialization (prepare_dataset.py "
            "--materialize), so the lost -> found matching task has exact "
            "ground-truth pairs."
        ),
        "taxonomy": {
            "top_level": ["PERSON", "PET", "ITEM", "VEHICLE", "DOCUMENT", "OTHER"],
            "subcategories": {
                "PET": ["dog", "cat", "bird", "rabbit", "other"],
                "ITEM": ["mobile", "laptop", "bag", "wallet", "watch", "keys",
                         "bicycle", "other"],
                "VEHICLE": ["car", "motorcycle", "bicycle", "other"],
            },
            "category_map": {key: list(value) for key, value in CATEGORY_MAP.items()},
        },
        "ground_truth_protocol": (
            "MATCH iff two cases share entity_id. The source corpus holds one "
            "photograph per subject, so a found report is a second viewpoint of "
            "the same photograph rather than an independent capture. Positives "
            "therefore test viewpoint/photometry invariance, not cross-session "
            "re-identification."
        ),
        "image_root": "../../Week-04",
        "source": {
            "metadata": "../../Week-04/metadata.json",
            "images": "../../Week-04/data",
        },
        "locations": locations,
        "entities": len(cases),
        "cases": cases,
    }
    CASES_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {CASES_PATH} with {len(cases)} cases")


if __name__ == "__main__":
    main()