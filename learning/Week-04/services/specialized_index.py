"""Separate Face FAISS and metadata/OCR indexes.

Face vectors never enter the CLIP index. OCR is represented as a small
inverted index over normalized tokens because exact identifiers are more
useful than semantic vector similarity for names, labels, and plates.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import faiss
import numpy as np

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokens(value):
    return set(TOKEN_RE.findall(str(value).lower()))


class SpecializedIndex:
    def __init__(self, metadata, face_index_path=None, face_names_path=None, ocr_path=None):
        self.metadata = metadata
        self.face_index_path = Path(face_index_path) if face_index_path else None
        self.face_names_path = Path(face_names_path) if face_names_path else None
        self.ocr_path = Path(ocr_path) if ocr_path else None
        self.face_index = None
        self.face_case_ids = []
        self.ocr_index = defaultdict(set)
        self._load_face()
        self._load_ocr()
        if not self.ocr_index:
            for case_id, record in metadata.items():
                self.index_ocr(case_id, self._metadata_text(record), persist=False)
            self._persist_ocr()

    @staticmethod
    def _metadata_text(record):
        return " ".join(str(record.get(field) or "") for field in ("title", "description", "notes", "ocr_text"))

    def _load_face(self):
        if self.face_index_path and self.face_index_path.exists():
            self.face_index = faiss.read_index(str(self.face_index_path))
        if self.face_names_path and self.face_names_path.exists():
            self.face_case_ids = [
                line.strip() for line in self.face_names_path.read_text().splitlines() if line.strip()
            ]

    def _load_ocr(self):
        if self.ocr_path and self.ocr_path.exists():
            data = json.loads(self.ocr_path.read_text())
            self.ocr_index = defaultdict(set, {key: set(value) for key, value in data.items()})

    def _persist_ocr(self):
        if self.ocr_path:
            self.ocr_path.parent.mkdir(parents=True, exist_ok=True)
            self.ocr_path.write_text(json.dumps({
                key: sorted(value) for key, value in self.ocr_index.items()
            }, indent=2))

    def index_ocr(self, case_id, text, persist=True):
        for token in tokens(text):
            self.ocr_index[token].add(case_id)
        if persist:
            self._persist_ocr()

    def search_ocr(self, text):
        query_tokens = tokens(text)
        if not query_tokens:
            return {}
        scores = defaultdict(float)
        for token in query_tokens:
            for case_id in self.ocr_index.get(token, set()):
                scores[case_id] += 1.0
        return {
            case_id: score / len(query_tokens)
            for case_id, score in scores.items()
        }

    def add_face(self, case_id, embeddings):
        vectors = [
            np.asarray(vector, dtype=np.float32).reshape(-1)
            for vector in embeddings
        ]
        if not vectors:
            return
        dimension = len(vectors[0])
        if self.face_index is None:
            self.face_index = faiss.IndexFlatIP(dimension)
        matrix = np.asarray(vectors, dtype=np.float32)
        faiss.normalize_L2(matrix)
        self.face_index.add(matrix)
        self.face_case_ids.extend([case_id] * len(vectors))
        if self.face_index_path:
            self.face_index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.face_index, str(self.face_index_path))
        if self.face_names_path:
            self.face_names_path.parent.mkdir(parents=True, exist_ok=True)
            self.face_names_path.write_text("\n".join(self.face_case_ids) + "\n")

    def search_faces(self, embeddings, top_k=50):
        if self.face_index is None or not embeddings:
            return {}
        query = np.asarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(query)
        similarities, indices = self.face_index.search(query, min(top_k, self.face_index.ntotal))
        scores = {}
        for row_scores, row_indices in zip(similarities, indices):
            for score, index in zip(row_scores, row_indices):
                if index >= 0:
                    case_id = self.face_case_ids[index]
                    scores[case_id] = max(scores.get(case_id, -1.0), float(score))
        return scores

    def retrieve(self, text=None, face_embeddings=None, top_k=50):
        ocr_scores = self.search_ocr(text or "")
        face_scores = self.search_faces(face_embeddings or [], top_k=top_k)
        case_ids = set(ocr_scores) | set(face_scores)
        return case_ids, ocr_scores, face_scores
