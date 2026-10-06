"""Generate normalized 512-D CLIP embeddings for every case image.

Reads metadata.json, runs each case image through the CLIP vision encoder
once (offline), and saves one .npy vector per case to embeddings/.

Run from learning/Week-03:

    python generate_embeddings.py
"""

import json
import os

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDINGS_DIR = "embeddings"


def get_image_embedding(processor, model, image_path, device):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.vision_model(**inputs)
        image_features = outputs.pooler_output
        image_features = model.visual_projection(image_features)
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.cpu().numpy().astype(np.float32).flatten()


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {MODEL_NAME} on {device}...")
    model = CLIPModel.from_pretrained(MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    metadata = json.load(open("metadata.json"))
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    vectors = {}
    for case_id, record in metadata.items():
        image_path = record["image_path"]
        if not os.path.exists(image_path):
            print(f"⚠️  Skipping {case_id}: {image_path} not found")
            continue
        emb = get_image_embedding(processor, model, image_path, device)
        out = os.path.join(EMBEDDINGS_DIR, f"{case_id}.npy")
        np.save(out, emb)
        vectors[case_id] = emb.shape[0]
        print(f"✅ {case_id} -> {out} (dim {emb.shape[0]})")

    print(f"\n🎉 Generated {len(vectors)} embeddings.")


if __name__ == "__main__":
    main()