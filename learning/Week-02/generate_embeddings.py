import os
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# ==========================================
# 1. Load CLIP model (same as before)
# ==========================================
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model.eval()

# ==========================================
# 2. Function to get embedding (copied from your code)
# ==========================================
def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model.vision_model(**inputs)
        image_features = outputs.pooler_output
        image_features = model.visual_projection(image_features)

    # Normalize
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.cpu().numpy().flatten()  # Flatten to 512-dim vector

# ==========================================
# 3. Generate and save embeddings for all cases
# ==========================================
os.makedirs("embeddings", exist_ok=True)

for i in range(1, 11):
    case_name = f"Case-{i:02d}"  # Case-01, Case-02, ... Case-10
    image_path = f"images/{case_name}.jpg"
    output_path = f"embeddings/{case_name}.npy"

    if not os.path.exists(image_path):
        print(f"⚠️ Warning: {image_path} not found. Skipping.")
        continue

    embedding = get_image_embedding(image_path)
    np.save(output_path, embedding)
    print(f"✅ Saved {output_path} (shape: {embedding.shape})")

print("\n🎉 All case embeddings generated successfully!")