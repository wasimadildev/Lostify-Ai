"""OCR evidence for the ranker, reusing the Week 04 PaddleOCR extractor.

The roadmap predicts the ranking strategy should depend on case type: "Item with
serial/name: OCR is the strong signal". Measured on this corpus that is exactly
right, and it is also *absent* elsewhere -- pets produce no text at all. So OCR
returns `None` when a pair has no readable text, which is a different fact from
scoring zero.

    python ocr_text.py            # extract and cache text for every case
"""

import json
import re
import sys
from pathlib import Path

WEEK05 = Path(__file__).resolve().parent.parent
WEEK04 = WEEK05.parent / "Week-04"
sys.path.insert(0, str(WEEK04 / "02-ocr"))
sys.path.insert(0, str(WEEK05 / "02-data-preparation"))

from prepare_dataset import (  # noqa: E402
    MODELS_DIR,
    load_cases,
    resolve_image,
    top_level_category,
)

CACHE = MODELS_DIR / "ocr" / "case_text.json"

# PaddleOCR hallucinates short glyphs on textured backgrounds; below this
# confidence a token is noise, not evidence.
MIN_CONFIDENCE = 0.60
_TOKEN = re.compile(r"[A-Z0-9]+")


def _extract(path):
    from ocr import extract_text

    try:
        blocks = extract_text(path)
    except Exception as exc:  # one unreadable image must not lose the cache
        return {"status": "error", "detail": str(exc)[:120], "tokens": []}
    tokens = []
    for block in blocks or []:
        value = str(block.get("value", ""))
        confidence = float(block.get("confidence", 0.0))
        for match in _TOKEN.findall(value.upper()):
            tokens.append({
                "text": match,
                "raw": value,
                "confidence": round(confidence, 4),
                "reliable": confidence >= MIN_CONFIDENCE,
            })
    return {"status": "ok", "tokens": tokens}


def build_cache(force=False):
    """Extract text for every case, resuming from the cache on each run.

    PaddleOCR takes ~10s per image, so a cold run over 92 cases exceeds a
    comfortable single command. The cache is rewritten after every case, which
    makes the work interruptible and resumable rather than all-or-nothing.
    """
    existing = {} if force else json.loads(CACHE.read_text() if CACHE.exists() else "{}")
    records = existing.get("records", {})
    todo = [c for c in load_cases() if c["case_id"] not in records]
    if todo:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
    categories = {c["case_id"]: top_level_category(c) for c in load_cases()}

    for index, case in enumerate(todo, start=1):
        records[case["case_id"]] = _extract(resolve_image(case))
        _write(records, categories)
        print(f"  ocr {index}/{len(todo)} {case['case_id']}", file=sys.stderr, flush=True)

    return _summary(records, categories)


def _write(records, categories):
    payload = _summary(records, categories)
    payload["records"] = records
    CACHE.write_text(json.dumps(payload, indent=2) + "\n")


def _summary(records, categories):
    reliable = {
        cid for cid, record in records.items()
        if any(t["reliable"] for t in record.get("tokens", []))
    }
    seen = set(categories.values())
    return {
        "min_confidence": MIN_CONFIDENCE,
        "cases": len(records),
        "with_text": len(reliable),
        "by_category": {
            category: sum(
                1 for cid in reliable if categories.get(cid) == category
            )
            for category in sorted(seen)
        },
    }


def load_cache():
    return build_cache()


def _reliable(record):
    return {token["text"] for token in record.get("tokens", []) if token["reliable"]}


def score_pair(left_record, right_record):
    """Shared readable text, confidence-weighted. None when there is no text."""
    left, right = _reliable(left_record), _reliable(right_record)
    if not left or not right:
        return None
    shared = left & right
    if not shared:
        return 0.0
    # A shared serial is far stronger evidence than one shared brand word.
    return round(min(len(shared) / min(len(left), len(right)), 1.0), 4)


def score_cases(left_id, right_id, cache=None):
    """Pairwise OCR score by case id. None when either side has no readable text."""
    cache = cache if cache is not None else load_cache()["records"]
    return score_pair(cache.get(left_id, {}), cache.get(right_id, {}))


def main():
    payload = build_cache()
    summary = {k: v for k, v in payload.items() if k != "records"}
    print(json.dumps(summary, indent=2))
    print(f"cache: {CACHE}")


if __name__ == "__main__":
    main()