"""Prove the FAISS serving path agrees with the NumPy evaluation path.

faiss and torch both link an OpenMP runtime, and importing both into one
process aborts with `OMP: Error #15`. The week therefore evaluates with exact
NumPy cosine search and serves with FAISS in a torch-free process -- which is
what this script simulates and then checks.

    python verify_faiss.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEEK05 / "04-clip"))

from clip_model import load_cache  # noqa: E402
from prepare_dataset import METRICS_DIR, is_found, load_cases  # noqa: E402

REPORT = METRICS_DIR / "faiss_agreement.json"


def verify(index_kind="FlatIP", k=10):
    try:
        import faiss
    except ImportError as exc:
        raise SystemExit("faiss-cpu is required. See requirements-week05.txt.") from exc

    embeddings, manifest = load_cache()
    cases = load_cases()
    found = [case for case in cases if is_found(case)]
    lost = [case for case in cases if not is_found(case)]

    rows = {case["case_id"]: position for position, case in enumerate(cases)}
    index_vectors = np.ascontiguousarray(embeddings[[rows[c["case_id"]] for c in found]])
    query_vectors = np.ascontiguousarray(embeddings[[rows[c["case_id"]] for c in lost]])

    index = faiss.IndexFlatIP(index_vectors.shape[1])
    index.add(index_vectors)
    faiss_scores, faiss_ids = index.search(query_vectors, min(k, len(found)))

    exact_scores = query_vectors @ index_vectors.T
    exact_order = np.argsort(-exact_scores, axis=1)[:, : k]
    exact_top = np.take_along_axis(exact_scores, exact_order, axis=1)

    started = time.perf_counter()
    for _ in range(20):
        index.search(query_vectors[:8], k)
    faiss_ms = (time.perf_counter() - started) * 1000 / (20 * 8)

    started = time.perf_counter()
    for _ in range(20):
        query_vectors[:8] @ index_vectors.T
    numpy_ms = (time.perf_counter() - started) * 1000 / (20 * 8)

    agreement = float(np.mean(faiss_ids[:, 0] == exact_order[:, 0]))
    max_gap = float(np.max(np.abs(faiss_scores[:, 0] - exact_top[:, 0])))

    return {
        "index": index_kind,
        "candidates": int(index_vectors.shape[0]),
        "queries": int(query_vectors.shape[0]),
        "top1_agreement": round(agreement, 4),
        "max_top1_score_gap": round(max_gap, 8),
        "faiss_ms_per_query": round(faiss_ms, 4),
        "numpy_ms_per_query": round(numpy_ms, 4),
        "numpy_faster_at_this_scale": bool(numpy_ms < faiss_ms),
        "note": (
            "exact agreement means the FAISS serving path is safe to ship. "
            "NumPy is faster only because the candidate pool is tiny; FAISS wins "
            "as the catalog grows, which is why the serving layer keeps it."
        ),
    }


def main():
    report = verify()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["top1_agreement"] < 1.0 or report["max_top1_score_gap"] > 1e-5:
        raise SystemExit("FAISS disagrees with exact search; the serving path is unsafe.")


if __name__ == "__main__":
    main()