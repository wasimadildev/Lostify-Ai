"""Build and save the FAISS index for the Week 03 case embeddings.

Loads every embeddings/<case_id>.npy vector, L2-normalizes them, and writes:

- embeddings/index.index      FAISS IndexFlatIP (inner product == cosine)
- embeddings/case_names.txt   case ids in index order

Run from learning/Week-03:

    python build_faiss_index.py
"""

import os

import faiss
import numpy as np

EMBEDDINGS_DIR = "embeddings"
INDEX_PATH = os.path.join(EMBEDDINGS_DIR, "index.index")
NAMES_PATH = os.path.join(EMBEDDINGS_DIR, "case_names.txt")


def main():
    case_names = []
    vectors = []
    for filename in sorted(os.listdir(EMBEDDINGS_DIR)):
        if filename.endswith(".npy"):
            vectors.append(np.load(os.path.join(EMBEDDINGS_DIR, filename)))
            case_names.append(filename.replace(".npy", ""))

    if not vectors:
        raise SystemExit("No embeddings found. Run generate_embeddings.py first.")

    embeddings = np.vstack(vectors).astype(np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(NAMES_PATH, "w") as f:
        f.write("\n".join(case_names) + "\n")

    print(f"✅ FAISS index saved to {INDEX_PATH}")
    print(f"   Vectors: {index.ntotal}  Dimension: {index.d}  Index type: FlatIP")


if __name__ == "__main__":
    main()