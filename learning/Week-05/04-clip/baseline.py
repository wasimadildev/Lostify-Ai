"""The measurement that decides whether CLIP needs fine-tuning at all.

Week 05's rule: *"Fine-tuning should only be done when your baseline evaluation
shows a real domain gap and you have enough labeled data to justify it."*
This script produces the "before" half of that comparison.

    python baseline.py                    # both protocols, val + test
    python baseline.py --protocol split   # split-disjoint only

Writes outputs/metrics/baseline_results.json.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

from clip_model import MODEL_ID, load_cache  # noqa: E402
from prepare_dataset import (  # noqa: E402
    METRICS_DIR, TEST, TRAIN, VALIDATION, is_found, load_cases, load_split,
)

REPORT = METRICS_DIR / "baseline_results.json"
TOP_K = (1, 5, 10)


def rows_for(cases, case_ids, entity_ids, embeddings):
    return np.array([case_ids.index(case["case_id"]) for case in cases]), np.array(
        [entity_ids.index(case["entity_id"]) for case in cases]
    )


def faiss_index(vectors):
    """Optional FAISS path. Returns None when FAISS is unavailable or unsafe here.

    faiss and torch both ship an OpenMP runtime, and importing both into one
    process aborts with "OMP: Error #15". Week 05 evaluation therefore uses
    exact NumPy cosine search -- which for a 46-candidate index is both faster
    and exactly correct -- and `verify_faiss.py` exercises FAISS in a torch-free
    process for the serving path.
    """
    return None


def search(index, queries, candidates, k):
    """Top-k neighbours as (scores, indices), FAISS or exact NumPy."""
    if index is None:
        scores = queries @ candidates.T
        order = np.argsort(-scores, axis=1)[:, :k]
        return np.take_along_axis(scores, order, axis=1), order
    return index.search(np.ascontiguousarray(queries), k)


def evaluate_protocol(name, queries, candidates, embeddings, manifest):
    case_ids = manifest["case_ids"]
    entity_ids = manifest["entity_ids"]

    q_rows, q_entities = rows_for(queries, case_ids, entity_ids, embeddings)
    c_rows, c_entities = rows_for(candidates, case_ids, entity_ids, embeddings)

    if not q_rows.size or not c_rows.size:
        return {"protocol": name, "available": False, "reason": "empty query or candidate set"}

    index = faiss_index(embeddings[c_rows])
    k = min(max(TOP_K), len(c_rows))
    started = time.perf_counter()
    scores, neighbours = search(index, embeddings[q_rows], embeddings[c_rows], k)
    search_ms = (time.perf_counter() - started) * 1000 / max(len(q_rows), 1)

    ranked = [c_entities[row] for row in neighbours]
    ranks = []
    hits = {k_k: 0 for k_k in TOP_K}
    for target, order in zip(q_entities, ranked):
        matches = np.flatnonzero(order == target)
        rank = int(matches[0]) + 1 if matches.size else len(order) + 1
        ranks.append(rank)
        for k_k in TOP_K:
            if rank <= k_k:
                hits[k_k] += 1

    total = len(ranks)
    return {
        "protocol": name,
        "available": True,
        "queries": total,
        "candidates": len(c_rows),
        "top_1": round(hits[1] / total, 4),
        "top_5": round(hits[5] / total, 4),
        "top_10": round(hits[10] / total, 4) if len(c_rows) >= 10 else None,
        "mrr": round(float(np.mean([1 / rank for rank in ranks])), 4),
        "mean_rank": round(float(np.mean(ranks)), 2),
        "median_rank": float(np.median(ranks)),
        "search_ms_per_query": round(search_ms, 3),
        "mean_top1_score": round(float(scores[:, 0].mean()), 4),
    }


def evaluate_pairs(embeddings, manifest):
    """Separability of the labelled pairs: positives vs negatives in one pool."""
    case_ids = manifest["case_ids"]
    entity_ids = manifest["entity_ids"]
    rows = np.array([case_ids.index(cid) for cid in case_ids])
    entity = np.array(entity_ids)
    similarity = embeddings[rows] @ embeddings[rows].T

    positive, negative = [], []
    upper = np.triu_indices(len(rows), k=1)
    for i, j in zip(*upper):
        (positive if entity[i] == entity[j] else negative).append(similarity[i, j])

    positive = np.array(positive)
    negative = np.array(negative)
    # AUC via the Mann-Whitney identity: no sklearn dependency.
    order = np.argsort(np.concatenate([negative, positive]), kind="mergesort")
    ranks = np.empty(len(order), dtype=float)
    ranks[order] = np.arange(1, len(order) + 1)
    n_neg, n_pos = len(negative), len(positive)
    auc = (ranks[n_neg:].sum() - n_pos * (n_pos + 1) / 2) / (n_neg * n_pos)

    return {
        "positive_pairs": n_pos,
        "negative_pairs": n_neg,
        "positive_mean": round(float(positive.mean()), 4),
        "positive_std": round(float(positive.std()), 4),
        "negative_mean": round(float(negative.mean()), 4),
        "negative_std": round(float(negative.std()), 4),
        "margin": round(float(positive.mean() - negative.mean()), 4),
        "auc": round(float(auc), 4),
    }


def measure_split_wide(embeddings, manifest, split):
    """Query every lost case of this split against this split's found cases."""
    cases = load_split(split)
    found = [c for c in cases if is_found(c)]
    lost = [c for c in cases if not is_found(c)]
    return evaluate_protocol(f"per_split/{split}", lost, found, embeddings, manifest)


def measure_catalog(embeddings, manifest):
    """Every lost case against every found case: the full 46-candidate pool."""
    cases = load_cases()
    found = [c for c in cases if is_found(c)]
    lost = [c for c in cases if not is_found(c)]
    return evaluate_protocol("catalog", lost, found, embeddings, manifest)


def measure_novel(embeddings, manifest, split, threshold):
    """Query unseen lost items against the *train* index only.

    Their true found view is deliberately not in the index, so there is no
    correct answer. What this measures is the failure mode that matters at
    serving time: how confidently does CLIP attach an unseen lost item to some
    unrelated seen candidate?
    """
    index_cases = [c for c in load_split(TRAIN) if is_found(c)]
    query_cases = [c for c in load_split(split) if not is_found(c)]
    return evaluate_novel(query_cases, index_cases, embeddings, manifest, threshold)


def evaluate_novel(queries, candidates, embeddings, manifest, threshold):
    """Novel-item false-match pressure: top-1 similarity with no true answer."""
    case_ids = manifest["case_ids"]
    entity_ids = manifest["entity_ids"]
    q_rows, _ = rows_for(queries, case_ids, entity_ids, embeddings)
    c_rows, _ = rows_for(candidates, case_ids, entity_ids, embeddings)
    if not q_rows.size or not c_rows.size:
        return {"available": False, "reason": "empty query or candidate set"}

    scores, _ = search(None, embeddings[q_rows], embeddings[c_rows], len(c_rows))
    top1 = scores[:, 0]
    return {
        "available": True,
        "queries": len(q_rows),
        "candidates": len(c_rows),
        "top1_mean": round(float(top1.mean()), 4),
        "top1_max": round(float(top1.max()), 4),
        "accept_threshold": round(float(threshold), 4),
        "would_accept": int((top1 >= threshold).sum()),
        "false_match_rate": round(float((top1 >= threshold).mean()), 4),
    }


def baseline(model_id=MODEL_ID, force_cache=False):
    if force_cache:
        from clip_model import build_cache

        build_cache(force=True)
    embeddings, manifest = load_cache()

    report = {
        "model": model_id,
        "device": manifest.get("device"),
        "dim": manifest["dim"],
        "embed_ms_per_image": manifest["embed_ms_per_image"],
        "search": "exact numpy cosine (faiss/torch OpenMP clash; see verify_faiss.py)",
        "protocols": {},
        "pairs": evaluate_pairs(embeddings, manifest),
    }

    # A defensible accept threshold: the positive-pair mean minus one standard
    # deviation. Novel items scoring above it would be false matches.
    pairs = report["pairs"]
    threshold = pairs["positive_mean"] - pairs["positive_std"]

    report["protocols"]["catalog"] = measure_catalog(embeddings, manifest)
    for split in (VALIDATION, TEST):
        report["protocols"][f"per_split/{split}"] = measure_split_wide(
            embeddings, manifest, split
        )
        report["protocols"][f"novel/{split}"] = measure_novel(
            embeddings, manifest, split, threshold
        )

    per_split = [
        report["protocols"][f"per_split/{split}"]
        for split in (VALIDATION, TEST)
        if report["protocols"][f"per_split/{split}"].get("available")
    ]
    catalog = report["protocols"]["catalog"]
    mean_top1 = float(np.mean([row["top_1"] for row in per_split])) if per_split else None
    report["headline"] = {
        "catalog_top_1": catalog.get("top_1"),
        "catalog_top_5": catalog.get("top_5"),
        "catalog_mrr": catalog.get("mrr"),
        "mean_per_split_top_1": round(mean_top1, 4) if mean_top1 is not None else None,
        "pair_auc": pairs["auc"],
        "search_ms_per_query": catalog.get("search_ms_per_query"),
        "accept_threshold": round(float(threshold), 4),
    }
    report["domain_gap"] = {
        "mean_top_1": round(mean_top1, 4) if mean_top1 is not None else None,
        "target_top_1": 0.85,
        "gap": round(0.85 - mean_top1, 4) if mean_top1 is not None else None,
        "pair_auc": pairs["auc"],
        "fine_tune_worthy": bool(mean_top1 is not None and mean_top1 < 0.85),
    }

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    return report


def render(report):
    lines = [
        f"CLIP baseline - {report['model']} ({report['device']}, {report['dim']}-d)",
        f"embedding {report['embed_ms_per_image']} ms/image",
        "",
        f"{'protocol':<28}{'n':>4}{'cand':>6}{'top1':>8}{'top5':>8}{'MRR':>8}{'ms/q':>8}",
        "-" * 70,
    ]
    for name, row in report["protocols"].items():
        if not row.get("available"):
            lines.append(f"{name:<28}{'n/a':>4}  {row.get('reason')}")
            continue
        if "false_match_rate" in row:
            lines.append(
                f"{name:<28}{row['queries']:>4}{row['candidates']:>6}"
                f"  false-match {row['false_match_rate']:.1%}"
                f" at threshold {row['accept_threshold']}"
                f" (top1 mean {row['top1_mean']})"
            )
            continue
        top10 = f"{row['top_10']:>8.3f}" if row.get("top_10") is not None else f"{'n/a':>8}"
        lines.append(
            f"{name:<28}{row['queries']:>4}{row['candidates']:>6}{row['top_1']:>8.3f}"
            f"{row['top_5']:>8.3f}{row['mrr']:>8.3f}{row['search_ms_per_query']:>8.2f}"
            f"   top10={top10.strip()}"
        )
    pairs = report["pairs"]
    lines += [
        "-" * 70,
        f"pairs      positive {pairs['positive_pairs']} mean {pairs['positive_mean']}"
        f" | negative {pairs['negative_pairs']} mean {pairs['negative_mean']}",
        f"separation margin {pairs['margin']}  AUC {pairs['auc']}",
    ]
    gap = report.get("domain_gap")
    if gap:
        lines += [
            "",
            f"domain gap : top-1 {gap['mean_top_1']} vs target {gap['target_top_1']}"
            f" (gap {gap['gap']})",
            f"verdict    : {'fine-tune is justified' if gap['fine_tune_worthy'] else 'keep frozen CLIP'}",
        ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", choices=["wide", "disjoint", "both"], default="both")
    parser.add_argument("--rebuild", action="store_true", help="re-embed the catalog")
    args = parser.parse_args()

    report = baseline(force_cache=args.rebuild)
    if args.protocol != "both":
        report["protocols"] = {
            name: row
            for name, row in report["protocols"].items()
            if not name.startswith(f"{args.protocol}/") and name != args.protocol
        }
    print(render(report))


if __name__ == "__main__":
    main()