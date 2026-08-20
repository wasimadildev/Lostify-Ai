import os
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# 1. Load CLIP model (only for QUERY image)
# ==========================================
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model.eval()

# ==========================================
# 2. Function to get embedding (same as before)
# ==========================================
def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model.vision_model(**inputs)
        image_features = outputs.pooler_output
        image_features = model.visual_projection(image_features)

    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.cpu().numpy().flatten()

# ==========================================
# 3. LOAD all precomputed case embeddings
# ==========================================
embedding_folder = "embeddings"
case_names = []
case_embeddings = []

for filename in sorted(os.listdir(embedding_folder)):
    if filename.endswith(".npy"):
        file_path = os.path.join(embedding_folder, filename)
        emb = np.load(file_path)          # Load the 512-dim vector
        case_embeddings.append(emb)
        case_names.append(filename.replace(".npy", ""))

# Convert to 2D array (10 cases x 512 dims)
case_embeddings = np.array(case_embeddings)
print(f"✅ Loaded {len(case_names)} case embeddings.")

# ==========================================
# 4. QUERY IMAGE (only CLIP inference here!)
# ==========================================
query_path = "images/query.jpg"
query_embedding = get_image_embedding(query_path)
query_embedding = query_embedding.reshape(1, -1)  # Reshape for cosine_similarity

# ==========================================
# 5. Compute similarities with loaded embeddings
# ==========================================
similarities = cosine_similarity(query_embedding, case_embeddings)[0]

# ==========================================
# 6. Pair results and sort
# ==========================================
results = [(case_names[i], similarities[i]) for i in range(len(case_names))]
results.sort(key=lambda x: x[1], reverse=True)

# ==========================================
# 7. Display all results
# ==========================================
print("\n==============================")
print("      LOSTIFY AI")
print("   IMAGE SIMILARITY SEARCH")
print("==============================\n")

print("Query:", query_path)
print("\nAll Cases:")

for case, score in results:
    print(f"{case} → {score:.4f}")

# ==========================================
# 8. Top 5 results
# ==========================================
top_5 = results[:5]

print("\n==============================")
print("        TOP 5 MATCHES")
print("==============================\n")

for rank, (case, score) in enumerate(top_5, start=1):
    print(f"{rank}. {case} → {score:.4f}")