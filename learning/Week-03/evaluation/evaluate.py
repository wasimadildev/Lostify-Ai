"""Week 03 evaluation runner (Day 6 deliverable).

Reads evaluation/test_dataset.json, runs every query through the real search
pipeline, and writes evaluation/results.json:

    - Top-1 / Top-5 / Top-10 accuracy (overall, by mode, by case type)
    - Mean reciprocal rank
    - Per-query details (rank of the expected case)
    - Latency: average FAISS search time and average total search time

Run from learning/Week-03:

    python evaluation/evaluate.py
"""

import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from engine import CLIPEngine  # noqa: E402
from evaluation.metrics import accuracy_at_k, mean_reciprocal_rank, reciprocal_rank  # noqa: E402

TEST_SET = BASE_DIR / "evaluation" / "test_dataset.json"
OUTPUT = BASE_DIR / "evaluation" / "results.json"


def load_test_set():
    data = json.loads(TEST_SET.read_text())
    return data["queries"]


def build_query(engine, item):
    """Return (kwargs, label) for engine.search from an evaluation item."""
    kwargs = {
        "text": item.get("text"),
        "query_type": item.get("query_type"),
        "category": item.get("category"),
        "location": item.get("location"),
        "top_k": 10,
    }
    if item.get("image"):
        image_path = BASE_DIR / item["image"]
        kwargs["image_bytes"] = image_path.read_bytes()
    return kwargs


def faiss_latency_ms(engine, samples=100):
    """Average FAISS index.search latency for the candidate pool."""
    rng = np.random.default_rng(0)
    query = rng.normal(size=512).astype(np.float32)
    query /= np.linalg.norm(query)
    start = time.perf_counter()
    for _ in range(samples):
        engine.store.search(query, 20)
    return (time.perf_counter() - start) / samples * 1000


def main():
    queries = load_test_set()
    engine = CLIPEngine()
    print(f"Engine ready: {len(engine.store)} cases in the index.\n")

    per_query = []
    total_ms = []

    for item in queries:
        kwargs = build_query(engine, item)
        started = time.perf_counter()
        results = engine.search(**kwargs)
        elapsed_ms = (time.perf_counter() - started) * 1000
        total_ms.append(elapsed_ms)

        ranked_ids = [r["case_id"] for r in results]
        expected = item["expected"]
        rank = next((i for i, cid in enumerate(ranked_ids, start=1) if cid in expected), None)

        record = {
            "query_id": item["query_id"],
            "mode": item["mode"],
            "case_type": item.get("query_type"),
            "text": item.get("text"),
            "expected": expected,
            "rank": rank,
            "hit@1": rank is not None and rank <= 1,
            "hit@5": rank is not None and rank <= 5,
            "hit@10": rank is not None and rank <= 10,
            "mrr": reciprocal_rank(ranked_ids, expected),
            "top_k_ids": ranked_ids,
            "latency_ms": round(elapsed_ms, 2),
        }
        per_query.append(record)
        tag = "OK" if rank is not None and rank <= 5 else "MISS"
        print(f"  [{tag}] {item['query_id']} ({item['mode']:<8}) rank {rank}  "
              f"expected {expected}  {elapsed_ms:.0f} ms")

    def summarize(items, label):
        results_pairs = [(it["top_k_ids"], it["expected"]) for it in items]
        if not results_pairs:
            return None
        return {
            "label": label,
            "total": len(items),
            "top1_accuracy": round(accuracy_at_k(results_pairs, 1), 4),
            "top5_accuracy": round(accuracy_at_k(results_pairs, 5), 4),
            "top10_accuracy": round(accuracy_at_k(results_pairs, 10), 4),
            "mrr": round(mean_reciprocal_rank(results_pairs), 4),
        }

    overall = summarize(per_query, "overall")
    by_mode = {mode: summarize([q for q in per_query if q["mode"] == mode], mode)
               for mode in ("image", "text", "combined")}
    by_type = {}
    for case_type in ("lost_pet", "lost_person", "lost_item"):
        subset = [q for q in per_query if q.get("case_type") == case_type]
        by_type[case_type] = summarize(subset, case_type)

    faiss_ms = faiss_latency_ms(engine)
    summary = {
        "dataset": str(TEST_SET),
        "overall": overall,
        "by_mode": {k: v for k, v in by_mode.items() if v},
        "by_case_type": {k: v for k, v in by_type.items() if v},
        "latency_ms": {
            "faiss_search_avg": round(faiss_ms, 3),
            "total_search_avg": round(statistics.mean(total_ms), 2),
            "total_search_p50": round(statistics.median(total_ms), 2),
            "total_search_p95": round(sorted(total_ms)[int(len(total_ms) * 0.95) - 1], 2),
        },
    }

    output = {"summary": summary, "per_query": per_query}
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print("\n" + "=" * 60)
    print("      WEEK 03 EVALUATION SUMMARY")
    print("=" * 60)
    for section in (overall, *[by_mode[m] for m in ("image", "text", "combined") if by_mode[m]],
                    *[by_type[t] for t in ("lost_pet", "lost_person", "lost_item") if by_type[t]]):
        if not section:
            continue
        print(f"\n  {section['label']:<10} n={section['total']}")
        print(f"    Top-1 : {section['top1_accuracy'] * 100:5.1f}%")
        print(f"    Top-5 : {section['top5_accuracy'] * 100:5.1f}%")
        print(f"    Top-10: {section['top10_accuracy'] * 100:5.1f}%")
        print(f"    MRR   : {section['mrr']:.4f}")
    print(f"\n  FAISS search  : {summary['latency_ms']['faiss_search_avg']:.3f} ms (avg)")
    print(f"  Total search  : {summary['latency_ms']['total_search_avg']:.2f} ms (avg)")
    print(f"\n✅ results written to {OUTPUT}")


if __name__ == "__main__":
    main()