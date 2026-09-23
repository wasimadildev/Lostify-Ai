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

# ===========================================
# ===========================================
#  Load Metadata (NEW STEP 6)
# ===========================================
# ===========================================


# import os
# import json
# import torch
# import numpy as np
# from PIL import Image
# from transformers import CLIPProcessor, CLIPModel
# from sklearn.metrics.pairwise import cosine_similarity

# # ==========================================
# # 1. Load CLIP model (only for QUERY image)
# # ==========================================
# model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
# model.eval()

# # ==========================================
# # 2. Load Metadata (NEW STEP 6)
# # ==========================================
# with open("metadata.json", "r") as f:
#     metadata = json.load(f)

# # ==========================================
# # 3. Function to get embedding
# # ==========================================
# def get_image_embedding(image_path):
#     image = Image.open(image_path).convert("RGB")
#     inputs = processor(images=image, return_tensors="pt")

#     with torch.no_grad():
#         outputs = model.vision_model(**inputs)
#         image_features = outputs.pooler_output
#         image_features = model.visual_projection(image_features)

#     image_features = image_features / image_features.norm(dim=-1, keepdim=True)
#     return image_features.cpu().numpy().flatten()

# # ==========================================
# # 4. LOAD all precomputed case embeddings
# # ==========================================
# embedding_folder = "embeddings"
# case_names = []
# case_embeddings = []

# for filename in sorted(os.listdir(embedding_folder)):
#     if filename.endswith(".npy"):
#         file_path = os.path.join(embedding_folder, filename)
#         emb = np.load(file_path)
#         case_embeddings.append(emb)
#         case_names.append(filename.replace(".npy", ""))

# case_embeddings = np.array(case_embeddings)
# print(f"✅ Loaded {len(case_names)} case embeddings.")

# # ==========================================
# # 5. QUERY IMAGE (only CLIP inference here!)
# # ==========================================
# query_path = "images/query.jpg"
# query_embedding = get_image_embedding(query_path)
# query_embedding = query_embedding.reshape(1, -1)

# # ==========================================
# # 6. Compute similarities
# # ==========================================
# similarities = cosine_similarity(query_embedding, case_embeddings)[0]

# # ==========================================
# # 7. Pair results and sort
# # ==========================================
# results = [(case_names[i], similarities[i]) for i in range(len(case_names))]
# results.sort(key=lambda x: x[1], reverse=True)

# # ==========================================
# # 8. Display all results (Optional)
# # ==========================================
# print("\n==============================")
# print("      LOSTIFY AI")
# print("   IMAGE SIMILARITY SEARCH")
# print("==============================\n")

# print("Query:", query_path)
# print("\nAll Cases (Scores):")
# for case, score in results:
#     print(f"{case} → {score:.4f}")

# # ==========================================
# # 9. TOP 5 WITH METADATA (NEW!)
# # ==========================================
# top_5 = results[:5]

# print("\n==============================")
# print("        TOP 5 MATCHES")
# print("==============================\n")

# for rank, (case, score) in enumerate(top_5, start=1):
#     # Fetch metadata for this case
#     case_data = metadata.get(case, {})
#     title = case_data.get("title", "Unknown Item")
#     category = case_data.get("category", "Unknown")
#     location = case_data.get("location", "Unknown")
#     description = case_data.get("description", "")

#     print(f"{rank}. {case} → Similarity: {score:.4f}")
#     print(f"   📌 {title} ({category})")
#     print(f"   📍 {location}")
#     print(f"   📝 {description}")
#     print("   " + "-" * 40)


# ==========================================
# Embedding + Metadata + Multimodal Search (Image + Text)
# ==========================================


# import os
# import json
# import torch
# import numpy as np
# from PIL import Image
# from transformers import CLIPProcessor, CLIPModel
# from sklearn.metrics.pairwise import cosine_similarity

# # ==========================================
# # 1. Load CLIP model
# # ==========================================
# model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
# model.eval()

# # ==========================================
# # 2. Load Metadata
# # ==========================================
# with open("metadata.json", "r") as f:
#     metadata = json.load(f)

# # ==========================================
# # 3. Embedding functions (Image + Text)
# # ==========================================
# def get_image_embedding(image_path):
#     image = Image.open(image_path).convert("RGB")
#     inputs = processor(images=image, return_tensors="pt")

#     with torch.no_grad():
#         outputs = model.vision_model(**inputs)
#         image_features = outputs.pooler_output
#         image_features = model.visual_projection(image_features)

#     image_features = image_features / image_features.norm(dim=-1, keepdim=True)
#     return image_features.cpu().numpy().flatten()

# def get_text_embedding(text):
#     """ NEW: Encode a text string into the same CLIP space """
#     inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)

#     with torch.no_grad():
#         outputs = model.text_model(**inputs)
#         text_features = outputs.pooler_output
#         text_features = model.text_projection(text_features)

#     text_features = text_features / text_features.norm(dim=-1, keepdim=True)
#     return text_features.cpu().numpy().flatten()

# # ==========================================
# # 4. Load precomputed case embeddings
# # ==========================================
# embedding_folder = "embeddings"
# case_names = []
# case_embeddings = []

# for filename in sorted(os.listdir(embedding_folder)):
#     if filename.endswith(".npy"):
#         file_path = os.path.join(embedding_folder, filename)
#         emb = np.load(file_path)
#         case_embeddings.append(emb)
#         case_names.append(filename.replace(".npy", ""))

# case_embeddings = np.array(case_embeddings)
# print(f"✅ Loaded {len(case_names)} case embeddings.\n")

# # ==========================================
# # 5. Search Function (supports image, text, or both)
# # ==========================================
# def search(query_image_path=None, query_text=None, weight_image=0.5, weight_text=0.5, top_k=5):
#     """
#     Search for similar cases using:
#     - query_image_path: path to an image file (or None)
#     - query_text: text description (or None)
#     - weight_image: how much to weight image similarity (0.0 to 1.0)
#     - weight_text: how much to weight text similarity (0.0 to 1.0)
#     """
#     # Normalize weights
#     total_weight = weight_image + weight_text
#     if total_weight == 0:
#         raise ValueError("At least one weight must be > 0")
#     weight_image = weight_image / total_weight
#     weight_text = weight_text / total_weight

#     # Initialize combined scores to zeros
#     combined_scores = np.zeros(len(case_names))

#     # ---- IMAGE QUERY ----
#     if query_image_path and weight_image > 0:
#         query_embedding = get_image_embedding(query_image_path)
#         query_embedding = query_embedding.reshape(1, -1)
#         image_similarities = cosine_similarity(query_embedding, case_embeddings)[0]
#         combined_scores += weight_image * image_similarities
#         print(f"🖼️  Image similarity computed for: {query_image_path}")

#     # ---- TEXT QUERY ----
#     if query_text and weight_text > 0:
#         query_embedding = get_text_embedding(query_text)
#         query_embedding = query_embedding.reshape(1, -1)
#         text_similarities = cosine_similarity(query_embedding, case_embeddings)[0]
#         combined_scores += weight_text * text_similarities
#         print(f"📝 Text similarity computed for: '{query_text}'")

#     # ---- Combine results ----
#     results = [(case_names[i], combined_scores[i]) for i in range(len(case_names))]
#     results.sort(key=lambda x: x[1], reverse=True)

#     # ---- Display Top K ----
#     top_results = results[:top_k]

#     print("\n" + "=" * 60)
#     print("        TOP {} MATCHES".format(top_k))
#     print("=" * 60 + "\n")

#     for rank, (case, score) in enumerate(top_results, start=1):
#         case_data = metadata.get(case, {})
#         title = case_data.get("title", "Unknown Item")
#         category = case_data.get("category", "Unknown")
#         location = case_data.get("location", "Unknown")
#         description = case_data.get("description", "")

#         print(f"{rank}. {case} → Combined Score: {score:.4f}")
#         print(f"   📌 {title} ({category})")
#         print(f"   📍 {location}")
#         print(f"   📝 {description}")
#         print("   " + "-" * 50)

#     return top_results

# # ==========================================
# # 6. DEMO: Test all three modes
# # ==========================================
# if __name__ == "__main__":
#     print("\n" + "=" * 60)
#     print("        LOSTIFY AI - STEP 7")
#     print("   IMAGE + TEXT MULTIMODAL SEARCH")
#     print("=" * 60)

#     # ---- MODE 1: Image-only search (same as before) ----
#     print("\n🔍 MODE 1: Image Search")
#     print("-" * 40)
#     search(query_image_path="images/query.jpg", weight_image=1.0, weight_text=0.0)

#     # ---- MODE 2: Text-only search ----
#     print("\n🔍 MODE 2: Text Search")
#     print("-" * 40)
#     search(query_text="lost dog with blue collar", weight_image=0.0, weight_text=1.0)

#     # ---- MODE 3: Combined Image + Text search ----
#     print("\n🔍 MODE 3: Combined Search (Image + Text)")
#     print("-" * 40)
#     search(
#         query_image_path="images/query.jpg",
#         query_text="lost dog with blue collar",
#         weight_image=0.5,
#         weight_text=0.5
#     )


# ==========================================
# 8. FAISS Index for Fast Search (NEW STEP 8)
# ==========================================



# import os
# import json
# import torch
# import numpy as np
# import faiss
# from PIL import Image
# from transformers import CLIPProcessor, CLIPModel

# # ==========================================
# # 1. Load CLIP model
# # ==========================================
# model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
# model.eval()

# # ==========================================
# # 2. Load Metadata
# # ==========================================
# with open("metadata.json", "r") as f:
#     metadata = json.load(f)

# # ==========================================
# # 3. Load FAISS index and case names
# # ==========================================
# index = faiss.read_index("embeddings.index")
# print(f"✅ Loaded FAISS index with {index.ntotal} vectors.")

# with open("embeddings_case_names.txt", "r") as f:
#     case_names = [line.strip() for line in f.readlines()]

# print(f"✅ Loaded {len(case_names)} case names.\n")

# # ==========================================
# # 4. Embedding functions (unchanged)
# # ==========================================
# def get_image_embedding(image_path):
#     image = Image.open(image_path).convert("RGB")
#     inputs = processor(images=image, return_tensors="pt")

#     with torch.no_grad():
#         outputs = model.vision_model(**inputs)
#         image_features = outputs.pooler_output
#         image_features = model.visual_projection(image_features)

#     image_features = image_features / image_features.norm(dim=-1, keepdim=True)
#     return image_features.cpu().numpy().astype(np.float32).flatten()

# def get_text_embedding(text):
#     inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True)

#     with torch.no_grad():
#         outputs = model.text_model(**inputs)
#         text_features = outputs.pooler_output
#         text_features = model.text_projection(text_features)

#     text_features = text_features / text_features.norm(dim=-1, keepdim=True)
#     return text_features.cpu().numpy().astype(np.float32).flatten()

# # ==========================================
# # 5. Search function using FAISS
# # ==========================================
# def search(query_image_path=None, query_text=None, weight_image=0.5, weight_text=0.5, top_k=5):
#     """
#     Search using FAISS index.
#     Returns top_k results with combined scores.
#     """
#     # Normalize weights
#     total_weight = weight_image + weight_text
#     if total_weight == 0:
#         raise ValueError("At least one weight must be > 0")
#     weight_image = weight_image / total_weight
#     weight_text = weight_text / total_weight

#     # Prepare a single query vector? 
#     # FAISS doesn't natively support weighted combination of separate embeddings.
#     # We'll compute two separate queries and then combine scores manually.
#     # This is still fast because we do two FAISS searches (or we can do one combined? 
#     # Actually we can combine by computing both embeddings, then combine before search? 
#     # The simplest: compute both similarities using FAISS separately and then combine.

#     # We'll store scores per case
#     combined_scores = np.zeros(len(case_names))

#     # ---- IMAGE QUERY ----
#     if query_image_path and weight_image > 0:
#         query_emb = get_image_embedding(query_image_path).reshape(1, -1)
#         # FAISS expects float32 and normalized
#         query_emb = query_emb.astype(np.float32)
#         faiss.normalize_L2(query_emb)  # ensure normalization

#         # Search FAISS: returns distances (similarity scores) and indices
#         distances, indices = index.search(query_emb, top_k)  # we could also search all and combine, but better to get all scores
#         # To combine, we need scores for all cases. Let's search for all (k = ntotal)
#         distances_all, indices_all = index.search(query_emb, index.ntotal)
#         # distances are inner products (cosine similarity if normalized)
#         # Map back to case index order
#         for i, idx in enumerate(indices_all[0]):
#             combined_scores[idx] += weight_image * distances_all[0][i]

#     # ---- TEXT QUERY ----
#     if query_text and weight_text > 0:
#         query_emb = get_text_embedding(query_text).reshape(1, -1)
#         query_emb = query_emb.astype(np.float32)
#         faiss.normalize_L2(query_emb)

#         distances_all, indices_all = index.search(query_emb, index.ntotal)
#         for i, idx in enumerate(indices_all[0]):
#             combined_scores[idx] += weight_text * distances_all[0][i]

#     # ---- Rank results ----
#     # Combine scores: we have combined_scores per original case index
#     # Create list of (case_name, score)
#     results = [(case_names[i], combined_scores[i]) for i in range(len(case_names))]
#     results.sort(key=lambda x: x[1], reverse=True)

#     # ---- Display Top K ----
#     top_results = results[:top_k]

#     print("\n" + "=" * 60)
#     print("        TOP {} MATCHES".format(top_k))
#     print("=" * 60 + "\n")

#     for rank, (case, score) in enumerate(top_results, start=1):
#         case_data = metadata.get(case, {})
#         title = case_data.get("title", "Unknown Item")
#         category = case_data.get("category", "Unknown")
#         location = case_data.get("location", "Unknown")
#         description = case_data.get("description", "")

#         print(f"{rank}. {case} → Combined Score: {score:.4f}")
#         print(f"   📌 {title} ({category})")
#         print(f"   📍 {location}")
#         print(f"   📝 {description}")
#         print("   " + "-" * 50)

#     return top_results

# # ==========================================
# # 6. DEMO
# # ==========================================
# if __name__ == "__main__":
#     print("\n" + "=" * 60)
#     print("        LOSTIFY AI - STEP 8")
#     print("   FAST SEARCH WITH FAISS")
#     print("=" * 60)

#     # Image-only
#     print("\n🔍 MODE 1: Image Search")
#     print("-" * 40)
#     search(query_image_path="images/query.jpg", weight_image=1.0, weight_text=0.0)

#     # Text-only
#     print("\n🔍 MODE 2: Text Search")
#     print("-" * 40)
#     search(query_text="lost dog with blue collar", weight_image=0.0, weight_text=1.0)

#     # Combined
#     print("\n🔍 MODE 3: Combined Search")
#     print("-" * 40)
#     search(
#         query_image_path="images/query.jpg",
#         query_text="lost dog with blue collar",
#         weight_image=0.5,
#         weight_text=0.5
#     )