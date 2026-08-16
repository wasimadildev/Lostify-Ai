import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity


# ==========================================
# 1. Load pretrained CLIP model
# ==========================================

model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
)

processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)

model.eval()


# ==========================================
# 2. Function to generate image embedding
# ==========================================

def get_image_embedding(image_path):

    image = Image.open(image_path).convert("RGB")

    inputs = processor(
        images=image,
        return_tensors="pt"
    )

    with torch.no_grad():

        outputs = model.vision_model(**inputs)

        image_features = outputs.pooler_output

        image_features = model.visual_projection(
            image_features
        )

    # Normalize
    image_features = image_features / image_features.norm(
        dim=-1,
        keepdim=True
    )

    return image_features.cpu().numpy()


# ==========================================
# 3. Generate embeddings
# ==========================================

cat1_embedding = get_image_embedding(
    "images/cat.jpeg"
)

cat2_embedding = get_image_embedding(
    "images/cat2.jpg"
)

dog_embedding = get_image_embedding(
    "images/dog.jpeg"
)


# ==========================================
# 4. Compare images
# ==========================================

cat_similarity = cosine_similarity(
    cat1_embedding,
    cat2_embedding
)[0][0]

dog_similarity = cosine_similarity(
    cat1_embedding,
    dog_embedding
)[0][0]


# ==========================================
# 5. Display results
# ==========================================

print("\n==============================")
print("   LOSTIFY AI SIMILARITY")
print("==============================\n")

print(
    f"Cat 1 ↔ Cat 2: {cat_similarity:.4f}"
)

print(
    f"Cat 1 ↔ Dog: {dog_similarity:.4f}"
)