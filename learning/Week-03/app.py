"""Lostify AI - Week 03 integrated FastAPI service (Day 7 deliverable).

One endpoint drives the whole pipeline:

    POST /search
      image       (file)     optional query image
      text        (string)   optional text description
      query_type  (string)   lost_pet | lost_item | lost_person
      category    (string)   controlled category (cat, dog, bicycle, ...)
      location    (string)   city name used for the location score
      top_k       (int)      number of results (default 5)
      weight_image / weight_text  fusion weights

At least one of image or text is required.

Run:

    python app.py            # http://localhost:8000, docs at /docs
"""

import os
import time

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import db
from engine import CLIPEngine, DEFAULT_TOP_K

app = FastAPI(
    title="Lostify AI Service - Week 03",
    description="Image + text similarity search with filtering, ranking, and explainable scores",
    version="3.1.0",
)

ALLOWED_QUERY_TYPES = {"lost_pet", "lost_item", "lost_person"}
TYPE_FOLDERS = {"lost_pet": "pets", "lost_person": "persons", "lost_item": "items"}

# Browser frontend (React dev server) talks to this API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the dataset images so the frontend can render case thumbnails
# (a stored image_path like "data/pets/PETS-01.jpg" maps to /static/pets/PETS-01.jpg).
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")

# Loaded once at startup
engine = CLIPEngine()
print(f"✅ Engine ready: {len(engine.store)} cases indexed, device={engine.device}")

# Database: create table + copy the static dataset in once (idempotent)
db.init_db()
seeded = db.seed_from_metadata()
print(f"✅ Database ready: {db.DB_PATH} ({seeded} reports stored)")


@app.get("/")
async def root(request: Request):
    # A browser hitting the site root gets the React app; an API client
    # (curl, or /docs) gets the service description below.
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.isdir(FRONTEND_DIST):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    return {
        "service": "Lostify AI - Week 03",
        "status": "online",
        "endpoints": [
            "GET /", "GET /health", "GET /cases", "GET /reports",
            "POST /reports", "POST /search",
        ],
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "CLIP ViT-B/32",
        "index_size": len(engine.store),
        "case_types": ["lost_pet", "lost_person", "lost_item"],
        "device": engine.device,
    }


@app.get("/cases")
async def list_cases(request: Request, limit: int = 200):
    # Browser navigation -> the app page; API/fetch call -> JSON (same as GET /)
    if "text/html" in request.headers.get("accept", "") and os.path.isdir(FRONTEND_DIST):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    cases = []
    for case_id, record in engine.store.metadata.items():
        cases.append({
            "case_id": case_id,
            "case_type": record.get("case_type"),
            "category": record.get("category"),
            "title": record.get("title"),
            "description": record.get("description"),
            "location": record.get("location"),
            "latitude": record.get("latitude"),
            "longitude": record.get("longitude"),
            "date_lost": record.get("date_lost"),
            "image_path": record.get("image_path"),
            "status": record.get("status"),
        })
    return {"count": len(cases), "data": cases[:limit]}


@app.get("/reports")
async def list_reports(request: Request, limit: int = 500):
    """Every report in the database: the seeded dataset + user submissions."""
    # Browser navigation -> the app's "All reports" page; fetch/curl -> JSON
    if "text/html" in request.headers.get("accept", "") and os.path.isdir(FRONTEND_DIST):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
    rows = db.list_reports(limit=limit)
    return {"count": len(rows), "data": rows}


@app.post("/reports")
async def create_report(
    image: UploadFile = File(None, description="Photo of the lost pet / person / item (optional if text given)"),
    title: str = Form(None, description="Short headline for the report"),
    description: str = Form(None, description="What went missing and the details"),
    case_type: str = Form(..., description="lost_pet | lost_item | lost_person"),
    category: str = Form(None, description="controlled category (cat, dog, bicycle, ...)"),
    location: str = Form(None, description="city / area of the loss"),
    latitude: float = Form(None, description="optional latitude"),
    longitude: float = Form(None, description="optional longitude"),
    date_lost: str = Form(None, description="optional ISO date, e.g. 2026-09-21"),
    status: str = Form("open", description="open | closed"),
):
    if case_type not in ALLOWED_QUERY_TYPES:
        raise HTTPException(status_code=400, detail=f"case_type must be one of {sorted(ALLOWED_QUERY_TYPES)}")

    image_bytes = None
    if image is not None and image.filename:
        image_bytes = await image.read()

    has_image = image_bytes not in (None, b"")
    has_text = bool((description or "").strip() or (title or "").strip())
    if not has_image and not has_text:
        raise HTTPException(status_code=400, detail="A new report needs a photo, a description, or a title.")

    # 1. New id + image file (kept out of the seeded folder paths)
    case_id = db.next_case_id(case_type)
    while case_id in engine.store.metadata:
        case_id = db.next_case_id(case_type)  # very unlikely collision guard

    folder = TYPE_FOLDERS.get(case_type, "uploads")
    image_path = None
    if has_image:
        relative = os.path.join("data", folder, f"{case_id}.jpg")
        absolute = os.path.join(DATA_DIR, folder, f"{case_id}.jpg")
        os.makedirs(os.path.dirname(absolute), exist_ok=True)
        with open(absolute, "wb") as f:
            f.write(image_bytes)
        image_path = relative

    record = {
        "case_id": case_id,
        "case_type": case_type,
        "category": (category or "").strip().lower() or None,
        "title": title or (description or "")[:60],
        "description": description,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "date_lost": date_lost,
        "image_path": image_path,
        "status": status,
    }

    # 2. Make it searchable right away (embed + add to FAISS + persist)
    try:
        engine.add_report(
            case_id=case_id,
            metadata=record,
            image_bytes=image_bytes,
            text=description or title,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"indexing error: {err}")

    # 3. Save to the database (long-term store)
    db.insert_report({**record, "source": "user"})

    return JSONResponse(
        status_code=201,
        content={
            "message": f"Report {case_id} saved and added to the search index. It is now findable via /search.",
            "case": record,
        },
    )


@app.post("/search")
async def search(
    image: UploadFile = File(None, description="Query image of the lost pet / person / item"),
    text: str = Form(None, description="Text description of the lost case"),
    query_type: str = Form(None, description="lost_pet | lost_item | lost_person"),
    category: str = Form(None, description="controlled category (cat, dog, bicycle, ...)"),
    location: str = Form(None, description="city / area where the loss happened"),
    top_k: int = Form(DEFAULT_TOP_K, description="number of results to return"),
    candidate_k: int = Form(20, description="FAISS candidate pool size before filtering"),
    weight_image: float = Form(0.7, description="fusion weight for the image embedding"),
    weight_text: float = Form(0.3, description="fusion weight for the text embedding"),
):
    if query_type and query_type not in ALLOWED_QUERY_TYPES:
        raise HTTPException(status_code=400, detail=f"query_type must be one of {sorted(ALLOWED_QUERY_TYPES)}")
    if top_k < 1 or top_k > 50:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")

    image_bytes = None
    if image is not None and image.filename:
        image_bytes = await image.read()

    has_image = image_bytes not in (None, b"")
    has_text = bool(text and text.strip())
    if not has_image and not has_text:
        raise HTTPException(status_code=400, detail="Provide an image, text, or both.")

    started = time.perf_counter()
    try:
        results = engine.search(
            image_bytes=image_bytes,
            text=text,
            query_type=query_type,
            category=category,
            location=location,
            top_k=top_k,
            candidate_k=candidate_k,
            weight_image=weight_image,
            weight_text=weight_text,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"search error: {err}")
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    return JSONResponse(content={
        "query": {
            "has_image": has_image,
            "text": text or None,
            "query_type": query_type,
            "category": category,
            "location": location,
        },
        "latency_ms": elapsed_ms,
        "count": len(results),
        "results": results,
    })


# ---------------------------------------------------------------------------
# Frontend (production): serve the built React app from frontend/dist so the
# whole system runs on a single origin. API routes above are registered first
# and always win; anything else falls back to the SPA (index.html) so that
# client-side routes like /new-report work on refresh.
# ---------------------------------------------------------------------------
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")),
        name="assets",
    )

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        # exact file exists -> serve it, otherwise hand control back to React
        file = os.path.join(FRONTEND_DIST, path)
        if path and os.path.isfile(file):
            return FileResponse(file)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)