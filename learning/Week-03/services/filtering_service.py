"""Metadata filtering (Week 03, Day 3).

FAISS returns visually similar cases, not necessarily the right *type* of
case. This service filters a candidate list using structured metadata so a
"lost white cat" query does not return white dogs, shirts, or cars.
"""


def filter_candidates(candidates, query_type=None, category=None, status=None):
    """Filter a list of candidate records by metadata fields.

    Parameters
    ----------
    candidates : list[dict]
        Candidate dicts, each containing at least ``case_type`` and
        ``category`` (plus ``status`` when status filtering is active).
    query_type : str, optional
        One of ``lost_pet`` / ``lost_person`` / ``lost_item``. When set, only
        cases of that type remain.
    category : str, optional
        A controlled category (e.g. ``cat``, ``bicycle``). When set, only
        cases of that category remain. Case-insensitive.
    status : str, optional
        e.g. ``open``. When set, only cases with that status remain.

    Returns
    -------
    list[dict]
        The filtered candidates, preserving FAISS ranking order.
    """
    filtered = list(candidates)

    if query_type:
        query_type = query_type.strip().lower()
        filtered = [c for c in filtered if c.get("case_type", "").lower() == query_type]

    if category:
        category = category.strip().lower()
        filtered = [
            c for c in filtered
            if c.get("category", "").strip().lower() == category
        ]

    if status:
        status = status.strip().lower()
        filtered = [c for c in filtered if c.get("status", "").lower() == status]

    return filtered