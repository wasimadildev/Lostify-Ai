"""Download the Week 03 case dataset images from freely-licensed sources.

Uses the Openverse API (openverse.org) which aggregates CC-licensed images from
Flickr, Wikimedia Commons, and other providers. Images are fetched from the
provider CDN and saved as 640px JPEGs under data/<case_type>/<case_id>.jpg.

Run from learning/Week-03:

    python download_dataset.py
"""

import json
import os
import sys
import time

import requests
from PIL import Image

DATA_DIR = "data"
API_URL = "https://api.openverse.org/v1/images/"
REQUEST_DELAY = 0.5


def search_results(search_term):
    """Return a list of image urls for the search term (relevance ordered)."""
    params = {
        "q": search_term,
        "license_type": "commercial",
        "source": "flickr",
        "page_size": 10,
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [item["url"] for item in data.get("results", []) if item.get("url")]


def download_to(url, dest):
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
    resp.raise_for_status()
    tmp = dest + ".tmp"
    with open(tmp, "wb") as f:
        f.write(resp.content)
    with Image.open(tmp) as im:
        im = im.convert("RGB")
        im.thumbnail((640, 640))
        im.save(dest, "JPEG", quality=90)
    os.remove(tmp)


def main():
    catalog = json.load(open("catalog.json"))
    downloaded = 0
    skipped = 0
    failed = []

    for case in catalog["cases"]:
        case_type = case["case_type"]
        case_id = case["case_id"]
        dest = os.path.join(DATA_DIR, case_type, f"{case_id}.jpg")

        if case.get("copy_from"):
            continue  # handled locally in create_metadata.py

        if os.path.exists(dest):
            skipped += 1
            continue

        term = case.get("search_term")
        if not term:
            continue

        try:
            urls = search_results(term)
        except Exception as e:  # noqa: BLE001
            failed.append((case_id, term, f"search error: {e}"))
            print(f"[FAIL] {case_id}: search error {e}")
            continue

        if not urls:
            failed.append((case_id, term, "no search results"))
            print(f"[FAIL] {case_id}: no results for '{term}'")
            continue

        ok = False
        for url in urls:
            try:
                download_to(url, dest)
                ok = True
                print(f"[OK]   {case_id} <- {url}")
                break
            except Exception as e:  # noqa: BLE001
                print(f"  .. {case_id}: {type(e).__name__}: {e}")
        if not ok:
            failed.append((case_id, term, "all candidates failed"))
        else:
            downloaded += 1
        time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 50)
    print(f"Downloaded: {downloaded}  Skipped (already present): {skipped}")
    if failed:
        print("Failed:")
        for case_id, term, reason in failed:
            print(f"  {case_id} ({term}): {reason}")
        return 1
    print("Dataset images complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())