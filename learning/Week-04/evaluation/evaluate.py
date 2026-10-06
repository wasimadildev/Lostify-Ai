"""Evaluate Week 04 pipeline retrieval and write results.json."""

import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR.parent / "Week-03"))
sys.path.insert(0, str(BASE_DIR / "05-ai-pipeline"))

from evaluation.metrics import accuracy_at_k, mean_reciprocal_rank, reciprocal_rank  # noqa: E402

DATASET = BASE_DIR / "evaluation" / "test_dataset.json"
OUTPUT = BASE_DIR / "evaluation" / "results.json"


def evaluate(pipeline, dataset=DATASET):
    queries = json.loads(Path(dataset).read_text())["queries"]
    records = []
    durations = []
    for query in queries:
        started = time.perf_counter()
        response = pipeline.run(text=query.get("text"), top_k=10)
        durations.append((time.perf_counter() - started) * 1000)
        ids = [item["case_id"] for item in response["results"]]
        reciprocal = reciprocal_rank(ids, query["expected"])
        rank = next(
            (index for index, case_id in enumerate(ids, start=1)
             if case_id in query["expected"]),
            None,
        )
        records.append({
            "query_id": query["query_id"],
            "expected": query["expected"],
            "rank": rank,
            "hit@1": rank is not None and rank <= 1,
            "hit@5": rank is not None and rank <= 5,
            "mrr": reciprocal,
            "top_k_ids": ids,
        })
    pairs = [(record["top_k_ids"], record["expected"]) for record in records]
    summary = {
        "total": len(records),
        "top1_accuracy": accuracy_at_k(pairs, 1),
        "top5_accuracy": accuracy_at_k(pairs, 5),
        "mrr": mean_reciprocal_rank(pairs),
        "average_latency_ms": sum(durations) / len(durations) if durations else 0.0,
    }
    return {"summary": summary, "per_query": records}


def main():
    from engine import CLIPEngine
    from pipeline import AIPipeline
    result = evaluate(AIPipeline(extractor=None, search_engine=CLIPEngine()))
    OUTPUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
