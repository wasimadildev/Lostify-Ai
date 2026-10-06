"""Dependency-free retrieval metrics (recall@k, MRR).

Same metric family as the original Week 03 mini evaluator. These functions
only consume Ranked case IDs and expected case IDs, so they are trivially
testable without CLIP, FAISS, or any running service.
"""


def is_hit_at(ranked_ids, expected_ids, k):
    """True if any expected id appears in the top-k of ranked_ids."""
    top_k = ranked_ids[:k]
    return any(expected in top_k for expected in expected_ids)


def recall_at_k(ranked_ids, expected_ids, k):
    """Fraction of expected ids found in the top-k of ranked_ids."""
    if not expected_ids:
        return 0.0
    top_k = set(ranked_ids[:k])
    found = sum(1 for expected in expected_ids if expected in top_k)
    return found / len(expected_ids)


def reciprocal_rank(ranked_ids, expected_ids):
    """1 / rank of the first expected id; 0.0 when no expected id is found."""
    for rank, case_id in enumerate(ranked_ids, start=1):
        if case_id in expected_ids:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(results):
    """Average reciprocal rank across multiple (ranked_ids, expected_ids) pairs."""
    if not results:
        return 0.0
    return sum(reciprocal_rank(ranked, expected) for ranked, expected in results) / len(results)


def accuracy_at_k(results, k):
    """Fraction of queries where any expected id appears in the top-k."""
    if not results:
        return 0.0
    hits = sum(1 for ranked, expected in results if is_hit_at(ranked, expected, k))
    return hits / len(results)