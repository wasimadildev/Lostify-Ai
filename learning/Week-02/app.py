import os
import json
import torch
import numpy as np
import faiss
from PIL import Image
from io import BytesIO
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import CLIPProcessor, CLIPModel
import uvicorn

# ==========================================
# 1. Initialize FastAPI
# ==========================================
app = FastAPI(
    title="Lostify AI Service",
    description="Image + Text similarity search for lost items",
    version="1.0.0"
)

# ==========================================
# 2. Load CLIP model (once at startup)
# ==========================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Loading CLIP model on {device}...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
model.to(device)
model.eval()
print("✅ CLIP model loaded.")

# ==========================================
# 3. Load FAISS index (once at startup)
# ==========================================
index = faiss.read_index("embeddings.index")
print(f"✅ FAISS index loaded with {index.ntotal} vectors.")

# Load case names (in the same order as the index)
with open("embeddings_case_names.txt", "r") as f:
    case_names = [line.strip() for line in f.readlines()]

# Load metadata
with open("metadata.json", "r") as f:
    metadata = json.load(f)

print(f"✅ Loaded {len(case_names)} cases with metadata.\n")

# ==========================================
# 4. Helper functions (embedding generation)
# ==========================================
def get_image_embedding_from_bytes(image_bytes: bytes):
    """Generate embedding from raw image bytes (uploaded file)."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.vision_model(**inputs)
        image_features = outputs.pooler_output
        image_features = model.visual_projection(image_features)

    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.cpu().numpy().astype(np.float32).flatten()

def get_text_embedding(text: str):
    """Generate embedding from text string."""
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(device)

    with torch.no_grad():
        outputs = model.text_model(**inputs)
        text_features = outputs.pooler_output
        text_features = model.text_projection(text_features)

    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return text_features.cpu().numpy().astype(np.float32).flatten()

# ==========================================
# 5. Core search function (using FAISS)
# ==========================================
def run_search(query_image_emb=None, query_text_emb=None, weight_image=0.5, weight_text=0.5, top_k=5):
    """Run FAISS search with optional image and/or text embeddings."""
    # Validate weights
    total_weight = weight_image + weight_text
    if total_weight == 0:
        raise ValueError("At least one weight must be > 0")
    weight_image = weight_image / total_weight
    weight_text = weight_text / total_weight

    combined_scores = np.zeros(len(case_names))

    # Image query
    if query_image_emb is not None and weight_image > 0:
        query_emb = query_image_emb.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_emb)
        distances, indices = index.search(query_emb, index.ntotal)  # get all scores
        for i, idx in enumerate(indices[0]):
            combined_scores[idx] += weight_image * distances[0][i]

    # Text query
    if query_text_emb is not None and weight_text > 0:
        query_emb = query_text_emb.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_emb)
        distances, indices = index.search(query_emb, index.ntotal)
        for i, idx in enumerate(indices[0]):
            combined_scores[idx] += weight_text * distances[0][i]

    # Sort and get top_k
    results = [(case_names[i], float(combined_scores[i])) for i in range(len(case_names))]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

# ==========================================
# 6. API Endpoints
# ==========================================

@app.get("/")
async def root():
    return {
        "service": "Lostify AI",
        "status": "online",
        "endpoints": ["GET /", "GET /health", "POST /search"],
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "CLIP ViT-B/32",
        "index_size": index.ntotal,
        "device": device
    }

@app.post("/search")
async def search(
    image: UploadFile = File(None, description="Upload an image of the lost item"),
    text: str = Form(None, description="Text description of the lost item"),
    weight_image: float = Form(0.5, description="Weight for image similarity (0.0 to 1.0)"),
    weight_text: float = Form(0.5, description="Weight for text similarity (0.0 to 1.0)"),
    top_k: int = Form(5, description="Number of top results to return")
):
    """
    Search for matching lost items using image, text, or both.
    
    - If only image is provided, weight_image will be set to 1.0 automatically.
    - If only text is provided, weight_text will be set to 1.0 automatically.
    - If both are provided, you can adjust weights for fine-tuning.
    """
    # Validate that at least one query type is provided
    if image is None and (text is None or text.strip() == ""):
        raise HTTPException(status_code=400, detail="Must provide either an image or text query.")

    # Auto-adjust weights if only one mode is used
    if image is None or image.filename == "":
        weight_image = 0.0
    if text is None or text.strip() == "":
        weight_text = 0.0

    if weight_image == 0 and weight_text == 0:
        raise HTTPException(status_code=400, detail="No valid query provided.")

    # Normalize weights
    total = weight_image + weight_text
    if total > 0:
        weight_image = weight_image / total
        weight_text = weight_text / total

    # Generate embeddings
    query_image_emb = None
    query_text_emb = None

    try:
        if weight_image > 0 and image is not None:
            image_bytes = await image.read()
            query_image_emb = get_image_embedding_from_bytes(image_bytes)
        
        if weight_text > 0 and text is not None and text.strip() != "":
            query_text_emb = get_text_embedding(text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

    # Run search
    try:
        top_results = run_search(
            query_image_emb=query_image_emb,
            query_text_emb=query_text_emb,
            weight_image=weight_image,
            weight_text=weight_text,
            top_k=top_k
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

    # Format response with metadata
    response_results = []
    for case_name, score in top_results:
        case_data = metadata.get(case_name, {})
        response_results.append({
            "case_id": case_name,
            "similarity_score": round(score, 4),
            "title": case_data.get("title", "Unknown Item"),
            "category": case_data.get("category", "Unknown"),
            "location": case_data.get("location", "Unknown"),
            "description": case_data.get("description", "")
        })

    return JSONResponse(content={
        "query": {
            "has_image": image is not None and image.filename != "",
            "text": text if text else None,
            "weight_image": weight_image,
            "weight_text": weight_text
        },
        "top_k": top_k,
        "results": response_results
    })

# ==========================================
# 7. Run the server (if executed directly)
# ==========================================
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # auto-restart on code changes (disable in production)
    )