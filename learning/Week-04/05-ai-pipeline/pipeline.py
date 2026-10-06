"""Run image analysis before the Week 03 CLIP/FAISS search engine."""

import importlib.util
import sys
from pathlib import Path

from PIL import Image


WEEK04 = Path(__file__).resolve().parent.parent
FEATURES_PATH = WEEK04 / "04-feature-extraction" / "feature_extractor.py"
RANKING_PATH = WEEK04 / "services" / "specialized_ranking.py"
spec = importlib.util.spec_from_file_location("week04_features", FEATURES_PATH)
features_module = importlib.util.module_from_spec(spec)
sys.modules["week04_features"] = features_module
spec.loader.exec_module(features_module)
ranking_spec = importlib.util.spec_from_file_location("week04_specialized_ranking", RANKING_PATH)
ranking_module = importlib.util.module_from_spec(ranking_spec)
sys.modules["week04_specialized_ranking"] = ranking_module
ranking_spec.loader.exec_module(ranking_module)


class AIPipeline:
    def __init__(self, extractor, search_engine, specialized_index=None):
        self.extractor = extractor
        self.search_engine = search_engine
        self.specialized_index = specialized_index

    def run(self, image_bytes=None, text=None, **search_options):
        if not image_bytes and not (text and text.strip()):
            raise ValueError("Provide an image, text, or both.")
        features = {}
        if image_bytes:
            if self.extractor is None:
                raise ValueError("An extractor is required when image_bytes is provided.")
            from io import BytesIO
            with Image.open(BytesIO(image_bytes)) as image:
                features = self.extractor.extract(image.convert("RGB"))
        enriched_text = self._ocr_text(features)
        search_text = " ".join(part for part in (text or "", enriched_text) if part).strip() or None
        results = self.search_engine.search(
            image_bytes=image_bytes,
            text=search_text,
            **search_options,
        )
        if self.specialized_index:
            case_ids, ocr_scores, face_scores = self.specialized_index.retrieve(
                text=search_text,
                face_embeddings=features.get("face_embeddings", []),
            )
            existing = {item["case_id"] for item in results}
            for case_id in case_ids - existing:
                results.append({
                    "case_id": case_id,
                    **self.search_engine.store.metadata_for(case_id),
                })
            results = ranking_module.rank_specialized(results, ocr_scores, face_scores)
            results = results[:search_options.get("top_k", 5)]
        return {"features": features, "results": results}

    @staticmethod
    def _ocr_text(features):
        values = []
        for entry in features.get("text", []):
            value = entry.get("value", "").strip()
            if value:
                values.append(value)
        return " ".join(values)
