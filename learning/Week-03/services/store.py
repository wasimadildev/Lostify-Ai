"""Shared loading helpers for the Week 03 search pipeline."""

import json
import os

import faiss
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

METADATA_PATH = os.path.join(BASE_DIR, "metadata.json")
INDEX_PATH = os.path.join(BASE_DIR, "embeddings", "index.index")
NAMES_PATH = os.path.join(BASE_DIR, "embeddings", "case_names.txt")


class CaseStore:
    """Holds the FAISS index, case names, and case metadata together."""

    def __init__(self, index_path=INDEX_PATH, names_path=NAMES_PATH, metadata_path=METADATA_PATH):
        self.index_path = index_path
        self.names_path = names_path
        self.metadata_path = metadata_path
        self.index = faiss.read_index(index_path)
        with open(names_path, "r") as f:
            self.case_names = [line.strip() for line in f if line.strip()]
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)

    def __len__(self):
        return self.index.ntotal

    def metadata_for(self, case_id):
        return self.metadata.get(case_id, {})

    def search(self, query_emb, top_k):
        """Return (indices, similarities) for the given unit-normalized vector."""
        query = np.asarray(query_emb, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query)
        return self.index.search(query, top_k)

    def nearest(self, query_emb, top_k):
        """Return a list of (case_id, similarity) sorted by similarity desc."""
        similarities, indices = self.search(query_emb, top_k)
        results = [(self.case_names[idx], float(sim)) for idx, sim in zip(indices[0], similarities[0])]
        return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]

    def add_case(self, case_id, embedding, metadata):
        """Append a newly reported case to the live index and persist it.

        Called by POST /reports so a user-submitted report becomes searchable
        immediately (no server restart, no overnight rebuild). All writes go to
        the same files this store was loaded from.
        """
        vector = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(vector)
        self.index.add(vector)

        if case_id not in self.case_names:
            self.case_names.append(case_id)
        self.metadata[case_id] = metadata

        # Persist all three artifacts so the case survives a restart.
        faiss.write_index(self.index, self.index_path)
        with open(self.names_path, "w") as f:
            f.write("\n".join(self.case_names) + "\n")
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        return case_id