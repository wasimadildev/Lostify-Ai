"""Build metadata.json for the Week 03 case dataset.

Reads the case catalog (catalog.json), copies any locally-available case
images from prior weeks into data/, and writes a rich metadata.json:

    {
      "case_id": "PETS-01",
      "case_type": "lost_pet",          # lost_pet | lost_person | lost_item
      "category": "cat",                # controlled set
      "title": "...",
      "description": "...",
      "location": "Islamabad",
      "latitude": 33.6844,
      "longitude": 73.0479,
      "date_lost": "2026-08-28",
      "image_path": "data/pets/PETS-01.jpg",
      "status": "open"
    }
"""

import json
import os
import shutil

CATALOG = "catalog.json"
METADATA = "metadata.json"
DATA_DIR = "data"
WEEK02_IMAGES = "../Week-02/images"

TYPE_FROM_FOLDER = {
    "pets": "lost_pet",
    "persons": "lost_person",
    "items": "lost_item",
}


def copy_source_image(case, catalog_dir):
    """For cases that reuse a Week-02 image, copy it into data/<folder>/."""
    source = case.get("copy_from")
    if not source:
        return
    dest = os.path.join(DATA_DIR, case["case_type"], f"{case['case_id']}.jpg")
    if os.path.exists(dest):
        return
    src = os.path.join(catalog_dir, WEEK02_IMAGES, source)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source image not found: {src}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)


def build():
    catalog = json.load(open(CATALOG))
    catalog_dir = os.path.dirname(os.path.abspath(__file__))
    locations = catalog["locations"]
    metadata = {}

    for case in catalog["cases"]:
        copy_source_image(case, catalog_dir)

        case_type = TYPE_FROM_FOLDER[case["case_type"]]
        lat, lon = locations[case["location"]]
        image_path = os.path.join(
            DATA_DIR, case["case_type"], f"{case['case_id']}.jpg"
        ).replace("\\", "/")

        metadata[case["case_id"]] = {
            "case_id": case["case_id"],
            "case_type": case_type,
            "category": case["category"],
            "title": case["title"],
            "description": case["description"],
            "location": case["location"],
            "latitude": lat,
            "longitude": lon,
            "date_lost": case["date_lost"],
            "image_path": image_path,
            "status": case.get("status", "open"),
        }

    with open(METADATA, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    counts = {}
    for record in metadata.values():
        counts[record["case_type"]] = counts.get(record["case_type"], 0) + 1

    print(f"✅ metadata.json written with {len(metadata)} cases.")
    for case_type, n in sorted(counts.items()):
        print(f"   {case_type}: {n}")
    return metadata


if __name__ == "__main__":
    build()