"""Explainable ranking for CLIP, OCR, face, and location evidence."""


def _unit_similarity(value):
    """Map cosine similarity from [-1, 1] to a stable [0, 1] score."""
    return max(0.0, min(1.0, (float(value) + 1.0) / 2.0))


def rank_specialized(candidates, ocr_scores=None, face_scores=None):
    ocr_scores = ocr_scores or {}
    face_scores = face_scores or {}
    active = {
        "visual": any(item.get("visual_score") is not None for item in candidates),
        "text": any(item.get("text_score") is not None for item in candidates),
        "face": bool(face_scores),
        "ocr": bool(ocr_scores),
    }
    weights = {"visual": 0.40, "text": 0.15, "face": 0.25, "ocr": 0.20}
    total_weight = sum(weight for name, weight in weights.items() if active[name]) or 1.0
    ranked = []
    for candidate in candidates:
        case_id = candidate["case_id"]
        visual = _unit_similarity(candidate.get("visual_score") or 0.0)
        text = _unit_similarity(candidate.get("text_score") or 0.0)
        face = _unit_similarity(face_scores[case_id]) if case_id in face_scores else 0.0
        ocr = float(ocr_scores.get(case_id, 0.0))
        final = sum((
            weights["visual"] * visual if active["visual"] else 0.0,
            weights["text"] * text if active["text"] else 0.0,
            weights["face"] * face if active["face"] else 0.0,
            weights["ocr"] * ocr if active["ocr"] else 0.0,
        )) / total_weight
        ranked.append({
            **candidate,
            "face_score": round(face, 4) if case_id in face_scores else None,
            "ocr_score": round(ocr, 4) if case_id in ocr_scores else None,
            "specialized_score": round(final, 4),
            "final_score": round(final, 4),
        })
    return sorted(ranked, key=lambda item: item["final_score"], reverse=True)
