"""Multimodal embedding fusion (Week 03, Day 5).

Combines an image embedding and a text embedding into one unit-normalized
vector so a single FAISS search is performed for image + text queries.
"""

import numpy as np


def combine_embeddings(image_emb=None, text_emb=None, weight_image=0.7, weight_text=0.3):
    """Fuse image and/or text embeddings into a single normalized vector.

    - Only image provided -> the image embedding (normalized).
    - Only text provided  -> the text embedding (normalized).
    - Both provided       -> weighted sum, then L2-normalized.
    """
    if image_emb is None and text_emb is None:
        raise ValueError("At least one of image_emb or text_emb must be provided.")

    if image_emb is None:
        return normalize(text_emb)
    if text_emb is None:
        return normalize(image_emb)

    total = weight_image + weight_text
    if total <= 0:
        raise ValueError("Weights must sum to more than zero.")
    weight_image = weight_image / total
    weight_text = weight_text / total

    combined = weight_image * np.asarray(image_emb, dtype=np.float32) \
        + weight_text * np.asarray(text_emb, dtype=np.float32)
    return normalize(combined)


def normalize(vector):
    vector = np.asarray(vector, dtype=np.float32).flatten()
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Cannot normalize a zero vector.")
    return vector / norm