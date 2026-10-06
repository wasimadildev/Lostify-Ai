"""Explainable ranking (Week 03, Day 4).

Turns the raw similarity scores into a weighted, explainable final score:

    final_score = 0.70 * visual + 0.20 * text + 0.10 * location

Every component score is kept separate in the response so a user can see why
a case matched.
"""

import math

WEIGHTS = {
    "visual": 0.70,
    "text": 0.20,
    "location": 0.10,
}

DEFAULT_WEIGHTS = {"visual": WEIGHTS["visual"], "text": WEIGHTS["text"], "location": WEIGHTS["location"]}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres between two coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def location_score(case, query_location, query_lat=None, query_lon=None):
    """Score how relevant a case's location is to the query location.

    - Exact city-name match -> 1.0
    - Otherwise a distance-based score that decays from 1.0 at 0 km to 0.0
      beyond 200 km.
    - No query location -> None (component is neutralised by the caller).
    """
    if not query_location and query_lat is None and query_lon is None:
        return None

    if query_location and case.get("location", "").strip().lower() == query_location.strip().lower():
        return 1.0

    if query_lat is not None and query_lon is not None:
        lat = case.get("latitude")
        lon = case.get("longitude")
        if lat is not None and lon is not None:
            distance = haversine_km(query_lat, query_lon, lat, lon)
            return max(0.0, min(1.0, 1.0 - distance / 200.0))
    return 0.0


def rank_candidates(candidates, visual_scores=None, text_scores=None, weights=None,
                    query_location=None, query_lat=None, query_lon=None):
    """Rank candidates by the weighted final score.

    Parameters
    ----------
    candidates : list[dict]
        Candidate records that carry ``case_id`` (and latitude/longitude).
    visual_scores, text_scores : dict[str, float], optional
        case_id -> similarity for each modality. Missing entries get 0.0.
    weights : dict, optional
        Overrides for visual / text / location weights.
    query_location, query_lat, query_lon
        Location context used for the location component.

    Returns
    -------
    list[dict]
        Candidates annotated with ``visual_score``, ``text_score``,
        ``location_score`` and ``final_score``, sorted by final_score desc.
    """
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    visual_scores = visual_scores or {}
    text_scores = text_scores or {}

    ranked = []
    for candidate in candidates:
        case_id = candidate["case_id"]
        visual = float(visual_scores.get(case_id, 0.0))
        text = float(text_scores.get(case_id, 0.0))
        loc = location_score(candidate, query_location, query_lat, query_lon)

        active_weights = []
        if visual_scores:
            active_weights.append(weights["visual"])
        if text_scores:
            active_weights.append(weights["text"])
        if loc is not None:
            active_weights.append(weights["location"])
        if not active_weights:
            raise ValueError("Cannot rank without at least one scoring signal.")

        total_weight = sum(active_weights)
        final = (
            (weights["visual"] * visual if visual_scores else 0.0)
            + (weights["text"] * text if text_scores else 0.0)
            + (weights["location"] * loc if loc is not None else 0.0)
        ) / total_weight

        ranked.append({
            **candidate,
            "visual_score": round(visual, 4) if visual_scores else None,
            "text_score": round(text, 4) if text_scores else None,
            "location_score": round(loc, 4) if loc is not None else None,
            "final_score": round(final, 4),
        })

    ranked.sort(key=lambda c: c["final_score"], reverse=True)
    return ranked