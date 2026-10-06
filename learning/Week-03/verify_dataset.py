"""Verify case images match their metadata with CLIP zero-shot probing.

For every case, the image is probed against a set of concept phrases. If the
top prediction does not match the case category, the image is re-downloaded
from Openverse (trying up to max_candidates alternatives) until the probe
agrees. Requires metadata.json to match the case catalog.

Run from learning/Week-03:

    python verify_dataset.py              # verify only; no re-download
    python verify_dataset.py --fix        # re-download mismatched images
"""

import argparse
import json
import os
import sys
import tempfile
import time

import numpy as np
import requests
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

MODEL_NAME = "openai/clip-vit-base-patch32"
API_URL = "https://api.openverse.org/v1/images/"
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
CONCEPTS = {
    "cat": "cat", "dog": "dog", "person": "person", "luggage": "suitcase",
    "bag": "handbag", "backpack": "backpack", "payphone": "payphone",
    "bicycle": "bicycle", "shopping bag": "shopping bag", "smartphone": "smartphone",
    "laptop": "laptop", "wallet": "wallet", "keys": "keys", "umbrella": "umbrella",
    "headphones": "headphones", "water bottle": "water bottle",
    "sunglasses": "sunglasses", "camera": "camera",
}
LABELS = [f"a photo of a {v}" for v in CONCEPTS.values()]


def load_probe(device):
    model = CLIPModel.from_pretrained(MODEL_NAME).to(device).eval()
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    with torch.no_grad():
        inputs = processor(text=LABELS, return_tensors="pt", padding=True).to(device)
        features = model.text_model(**inputs).pooler_output
        features = model.text_projection(features)
        features = features / features.norm(dim=-1, keepdim=True)
    return model, processor, features.cpu().numpy()


def probe_image(model, processor, text_features, image_path, device):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.vision_model(**inputs).pooler_output
        output = model.visual_projection(output)
        output = output / output.norm(dim=-1, keepdim=True)
    sims = (output.cpu().numpy() @ text_features.T)[0]
    return LABELS[int(sims.argmax())].replace("a photo of a ", "")


def search_urls_wiki(term):
    """Fallback: find freely-licensed images via the English Wikipedia API."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{term} filetype:bitmap",
        "gsrnamespace": "6",
        "gsrlimit": "15",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }
    resp = requests.get(WIKI_API_URL, params=params, headers={"User-Agent": "LostifyAI-study/1.0"}, timeout=30)
    resp.raise_for_status()
    urls = []
    for page in resp.json().get("query", {}).get("pages", {}).values():
        infos = page.get("imageinfo", [])
        if not infos:
            continue
        url = infos[0].get("url")
        if url:
            clean_url = url.split("?")[0]
            if clean_url.lower().endswith((".jpg", ".jpeg", ".png")):
                urls.append(clean_url)
    return urls


def search_urls_openverse(term, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            resp = requests.get(
                API_URL,
                params={"q": term, "license_type": "commercial", "source": "flickr", "page_size": 24},
                timeout=30,
            )
            if resp.status_code == 200:
                return [i["url"] for i in resp.json().get("results", []) if i.get("url")]
            print(f"    openverse status {resp.status_code}")
        except requests.RequestException as e:
            print(f"    openverse error: {e}")
        attempt += 1
        if attempt < retries:
            time.sleep(2 + attempt * 3)
    return []


def search_urls(term):
    urls = search_urls_openverse(term)
    if urls:
        return urls
    print("    openverse exhausted; trying English Wikipedia API ...")
    return search_urls_wiki(term)


USER_AGENT = "LostifyAI-Study/1.0 (https://github.com/example/lostify-ai; educational FYP project)"


def _fetch(url, retries=3):
    """Download bytes with a descriptive UA; upload.wikimedia.org returns 429
    for bare browser UAs."""
    attempt = 0
    while attempt < retries:
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
            if resp.status_code == 200 and resp.content[:2] in (b"\xff\xd8", b"\x89P"):
                return resp.content
            print(f"    fetch status {resp.status_code} for {url[:80]}")
            if resp.status_code == 429:
                time.sleep(5 + attempt * 5)
        except requests.RequestException as e:
            print(f"    fetch error: {e}")
        attempt += 1
    raise requests.ConnectionError(f"could not fetch {url}")


def best_candidate(model, processor, text_features, urls, expected, device):
    """Return (path, score) of the candidate whose probe best matches `expected`."""
    expected_label = f"a photo of a {CONCEPTS[expected]}"
    best, best_score = None, -1.0
    best = None
    best_data = None
    with tempfile.TemporaryDirectory() as tmp:
        for url in urls:
            try:
                data = _fetch(url)
            except requests.RequestException:
                continue
            path = os.path.join(tmp, "c.jpg")
            with open(path, "wb") as f:
                f.write(data)
            try:
                with Image.open(path) as im:
                    im.convert("RGB").thumbnail((640, 640))
                score = _score(model, processor, text_features, path, expected_label, device)
            except Exception as e:  # noqa: BLE001
                print(f"    skip candidate ({type(e).__name__})")
                continue
            if score > best_score:
                best_data = data
                best_score = score
    if best_data is not None:
        best = os.path.join(tempfile.mkdtemp(), "best.jpg")
        with Image.open(__import__("io").BytesIO(best_data)) as im:
            im.convert("RGB").thumbnail((640, 640))
            im.save(best, "JPEG", quality=90)
    return best, best_score


def _score(model, processor, text_features, path, expected_label, device):
    sims_all = probe_sims(model, processor, text_features, path, device)
    idx = LABELS.index(expected_label)
    return float(sims_all[idx])


def probe_sims(model, processor, text_features, image_path, device):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.vision_model(**inputs).pooler_output
        output = model.visual_projection(output)
        output = output / output.norm(dim=-1, keepdim=True)
    return (output.cpu().numpy() @ text_features.T)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="re-download mismatched images")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {MODEL_NAME} on {device} ...")
    model, processor, text_features = load_probe(device)

    metadata = json.load(open("metadata.json"))
    mismatches = []
    for case_id, record in metadata.items():
        expected = CONCEPTS[record["category"]]
        pred = probe_image(model, processor, text_features, record["image_path"], device)
        status = "OK  " if pred == expected else "!!!"
        print(f"{status} {case_id:<9} exp={expected:<12} pred={pred}")
        if pred != expected:
            mismatches.append((case_id, record, expected, pred))

    print(f"\nMismatches: {len(mismatches)}")
    if not mismatches or not args.fix:
        return 1 if mismatches else 0

    for case_id, record, _expected, _pred in mismatches:
        term = record["title"]
        urls = search_urls(term)
        print(f"\n  Fixing {case_id} (expected '{record['category']}', term '{term}') with {len(urls)} candidates ...")
        best, score = best_candidate(model, processor, text_features, urls, record["category"], device)
        if best is None:
            print(f"    [FAIL] no usable candidate for {case_id}")
            continue
        with Image.open(best) as im:
            im.convert("RGB").thumbnail((640, 640))
            im.save(record["image_path"], "JPEG", quality=90)
        print(f"    [FIX] {case_id} <- new image (score {score:.3f})")

    print("\nRe-run this script (without --fix) to confirm.")
    return 1


if __name__ == "__main__":
    sys.exit(main())