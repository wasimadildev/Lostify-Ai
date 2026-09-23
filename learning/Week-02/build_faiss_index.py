import os
import numpy as np
import faiss

# ==========================================
# 1. Load all .npy embeddings
# ==========================================
embedding_folder = "embeddings"
case_names = []
embeddings_list = []

for filename in sorted(os.listdir(embedding_folder)):
    if filename.endswith(".npy"):
        file_path = os.path.join(embedding_folder, filename)
        emb = np.load(file_path).astype(np.float32)  # FAISS expects float32
        embeddings_list.append(emb)
        case_names.append(filename.replace(".npy", ""))

# Convert to a 2D array (N x 512)
embeddings = np.array(embeddings_list).astype(np.float32)
print(f"Loaded {len(case_names)} embeddings, each with dimension {embeddings.shape[1]}")

# ==========================================
# 2. Create FAISS index (FlatIP = inner product)
# ==========================================
# Normalize vectors to unit length (so inner product = cosine similarity)
faiss.normalize_L2(embeddings)

# IndexFlatIP uses inner product (dot product) - works for normalized vectors
index = faiss.IndexFlatIP(embeddings.shape[1])   # 512 dimensions
index.add(embeddings)   # Add all embeddings to the index

# ==========================================
# 3. Save the index and the case names
# ==========================================
faiss.write_index(index, "embeddings.index")

# Save case names in same order as they were added
with open("embeddings_case_names.txt", "w") as f:
    for name in case_names:
        f.write(name + "\n")

print("✅ FAISS index saved to 'embeddings.index'")
print(f"   Index contains {index.ntotal} vectors.")
print("   Case names saved to 'embeddings_case_names.txt'")