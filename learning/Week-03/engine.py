"""The integrated Week 03 search engine.

Single place that couples CLIP embedding generation, FAISS candidate
retrieval, metadata filtering, and explainable ranking. Used both by the
FastAPI service (app.py), the standalone experiment script
(similarity_search.py), and the evaluation suite.
"""

from io import BytesIO

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from services.filtering_service import filter_candidates
from services.multimodal_service import combine_embeddings
from services.ranking_service import rank_candidates
from services.store import CaseStore

MODEL_NAME = "openai/clip-vit-base-patch32"
DEFAULT_TOP_K = 5
DEFAULT_CANDIDATES = 20


class CLIPEngine:
    def __init__(self, model_name=MODEL_NAME, store=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(model_name).to(self.device).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.store = store or CaseStore()

    # ------------------------------------------------------------------
    # Embedding generators (512-D, unit-normalized)
    # ------------------------------------------------------------------
    def image_embedding_from_bytes(self, image_bytes):
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        return self._image_embedding(image)

    def image_embedding_from_path(self, image_path):
        return self._image_embedding(Image.open(image_path).convert("RGB"))

    def _image_embedding(self, image):
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self.model.vision_model(**inputs).pooler_output
            output = self.model.visual_projection(output)
        return self._normalize(output)

    def text_embedding(self, text):
        inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            output = self.model.text_model(**inputs).pooler_output
            output = self.model.text_projection(output)
        return self._normalize(output)

    def _normalize(self, output):
        output = output / output.norm(dim=-1, keepdim=True)
        return output.cpu().numpy().astype(np.float32).flatten()

    # ------------------------------------------------------------------
    # Similarity maps (per case id, for the explainable scores)
    # ------------------------------------------------------------------
    def _similarity_map(self, embedding):
        similarities, indices = self.store.search(embedding, self.store.index.ntotal)
        return {
            self.store.case_names[idx]: float(sim)
            for idx, sim in zip(indices[0], similarities[0])
        }

    # ------------------------------------------------------------------
    # Full search
    # ------------------------------------------------------------------
    def search(self, image_bytes=None, text=None, query_type=None, category=None,
               status=None, location=None, query_lat=None, query_lon=None,
               top_k=DEFAULT_TOP_K, candidate_k=DEFAULT_CANDIDATES,
               weight_image=0.7, weight_text=0.3):
        has_image = image_bytes is not None
        has_text = text is not None and text.strip() != ""
        if not has_image and not has_text:
            raise ValueError("Provide an image, text, or both.")

        image_emb = self.image_embedding_from_bytes(image_bytes) if has_image else None
        text_emb = self.text_embedding(text.strip()) if has_text else None

        combined = combine_embeddings(image_emb, text_emb, weight_image, weight_text)

        candidates = []
        for case_id, sim in self.store.nearest(combined, candidate_k):
            metadata = self.store.metadata_for(case_id)
            candidates.append({
                "case_id": case_id,
                **metadata,
            })

        visual_scores = self._similarity_map(image_emb) if has_image else None
        text_scores = self._similarity_map(text_emb) if has_text else None

        filtered = filter_candidates(candidates, query_type=query_type, category=category, status=status)
        ranked = rank_candidates(
            filtered,
            visual_scores=visual_scores,
            text_scores=text_scores,
            query_location=location if location else None,
            query_lat=query_lat,
            query_lon=query_lon,
        )
        return ranked[:top_k]

    def add_report(self, case_id, metadata, image_bytes=None, text=None):
        """Embed a brand-new report and make it searchable immediately.

        Used by POST /reports so user-submitted cases join the live FAISS index
        (and the persisted index/metadata files) without restarting the service.
        """
        if image_bytes is not None:
            embedding = self.image_embedding_from_bytes(image_bytes)
        elif text is not None and text.strip():
            embedding = self.text_embedding(text.strip())
        else:
            raise ValueError("A new report needs an image or a text description to be searchable.")

        return self.store.add_case(case_id, embedding, metadata)