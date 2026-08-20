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
# 2. Generate image embedding
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

    # Normalize embedding
    image_features = image_features / image_features.norm(
        dim=-1,
        keepdim=True
    )

    return image_features.cpu().numpy()


# ==========================================
# 3. Query image
# ==========================================

query_path = "images/query.jpg"

query_embedding = get_image_embedding(
    query_path
)


# ==========================================
# 4. Case images
# ==========================================

cases = [
    "Case-01.jpg",
    "Case-02.jpg",
    "Case-03.jpg",
    "Case-04.jpg",
    "Case-05.jpg",
    "Case-06.jpg",
    "Case-07.jpg",
    "Case-08.jpg",
    "Case-09.jpg",
    "Case-10.jpg"
]


# ==========================================
# 5. Calculate similarity
# ==========================================

results = []

for case in cases:

    case_path = f"images/{case}"

    case_embedding = get_image_embedding(
        case_path
    )

    similarity = cosine_similarity(
        query_embedding,
        case_embedding
    )[0][0]

    results.append(
        (case, similarity)
    )


# ==========================================
# 6. Sort highest similarity first
# ==========================================

results.sort(
    key=lambda x: x[1],
    reverse=True
)


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

    print(
        f"{case} → {score:.4f}"
    )


# ==========================================
# 8. Top 5 results
# ==========================================

top_5 = results[:5]

print("\n==============================")
print("        TOP 5 MATCHES")
print("==============================\n")

for rank, (case, score) in enumerate(
    top_5,
    start=1
):

    print(
        f"{rank}. {case} → {score:.4f}"
    )