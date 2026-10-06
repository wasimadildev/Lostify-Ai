"""Production-oriented Week 04 API.

Run from ``learning/Week-04``:

    uvicorn app:app --host 0.0.0.0 --port 8000

The API keeps Week 03 CLIP/FAISS search and adds image analysis metadata from
YOLO, OCR, and face detection. Heavy models are initialized lazily on startup
only when their dependencies are installed.
"""

import importlib.util
import os
import sys
import time
from pathlib import Path

# PyTorch/FAISS and PaddlePaddle can load separate OpenMP runtimes on macOS.
# This compatibility flag must be set before either runtime is imported.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
WEEK03_DIR = BASE_DIR.parent / "Week-03"
sys.path.insert(0, str(WEEK03_DIR))
sys.path.insert(0, str(BASE_DIR / "05-ai-pipeline"))

import db as week03_db  # noqa: E402
from engine import CLIPEngine  # noqa: E402
from services.store import CaseStore  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pipeline_module = load_module("week04_pipeline", BASE_DIR / "05-ai-pipeline" / "pipeline.py")
features_module = load_module(
    "week04_features", BASE_DIR / "04-feature-extraction" / "feature_extractor.py"
)
specialized_module = load_module(
    "week04_specialized_index", BASE_DIR / "services" / "specialized_index.py"
)

DATA_DIR = BASE_DIR / "data"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
WEEK04_DB = BASE_DIR / "lostify.db"
ALLOWED_TYPES = {"lost_pet", "lost_item", "lost_person"}

app = FastAPI(
    title="Lostify AI - Week 04",
    version="4.0.0",
    description="Multimodal lost-and-found search with YOLO, OCR, face features, CLIP, and FAISS.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")

engine = None
pipeline = None
feature_extractor = None
specialized_index = None


@app.on_event("startup")
def initialize():
    global engine, pipeline, feature_extractor, specialized_index
    store = CaseStore(
        index_path=str(BASE_DIR / "embeddings" / "index.index"),
        names_path=str(BASE_DIR / "embeddings" / "case_names.txt"),
        metadata_path=str(BASE_DIR / "metadata.json"),
    )
    engine = CLIPEngine(store=store)
    specialized_index = specialized_module.SpecializedIndex(
        metadata=store.metadata,
        face_index_path=BASE_DIR / "embeddings" / "face.index",
        face_names_path=BASE_DIR / "embeddings" / "face_case_names.txt",
        ocr_path=BASE_DIR / "embeddings" / "ocr_index.json",
    )
    week03_db.init_db(str(WEEK04_DB))
    week03_db.seed_from_metadata(
        db_path=str(WEEK04_DB), metadata_path=str(BASE_DIR / "metadata.json")
    )
    pipeline = pipeline_module.AIPipeline(
        extractor=None,
        search_engine=engine,
        specialized_index=specialized_index,
    )


def ensure_engine():
    if engine is None or pipeline is None:
        raise HTTPException(status_code=503, detail="AI service is still starting.")


def ensure_feature_extractor():
    global feature_extractor
    ensure_engine()
    if feature_extractor is None:
        try:
            feature_extractor = features_module.build_default_extractor(engine)
            pipeline.extractor = feature_extractor
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return feature_extractor


@app.get("/health")
def health():
    ensure_engine()
    return {
        "status": "healthy",
        "version": app.version,
        "index_size": len(engine.store),
        "models": {
            "clip": True,
            "yolo": feature_extractor is not None and feature_extractor.object_detector is not None,
            "ocr": feature_extractor is not None and feature_extractor.ocr_extractor is not None,
            "face_detection": feature_extractor is not None and feature_extractor.face_detector is not None,
            "face_index": specialized_index is not None and specialized_index.face_index is not None,
            "ocr_index": specialized_index is not None and bool(specialized_index.ocr_index),
        },
    }


@app.get("/cases")
def cases(limit: int = 200):
    ensure_engine()
    return {"count": len(engine.store.metadata), "data": [
        {"case_id": case_id, **record}
        for case_id, record in list(engine.store.metadata.items())[:limit]
    ]}


@app.get("/reports")
def reports(limit: int = 500):
    return {"count": week03_db.count(str(WEEK04_DB)), "data": week03_db.list_reports(
        limit=limit, db_path=str(WEEK04_DB)
    )}


@app.post("/reports", status_code=201)
async def create_report(
    image: UploadFile | None = File(None),
    title: str | None = Form(None),
    description: str | None = Form(None),
    case_type: str = Form(...),
    category: str | None = Form(None),
    location: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    date_lost: str | None = Form(None),
):
    ensure_engine()
    if case_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"case_type must be one of {sorted(ALLOWED_TYPES)}")
    image_bytes = await image.read() if image and image.filename else None
    validate_image(image_bytes)
    if not image_bytes and not (title and title.strip()) and not (description and description.strip()):
        raise HTTPException(status_code=400, detail="Provide an image, title, or description.")

    case_id = week03_db.next_case_id(case_type, db_path=str(WEEK04_DB))
    while case_id in engine.store.metadata:
        case_id = week03_db.next_case_id(case_type, db_path=str(WEEK04_DB))
    image_path = None
    if image_bytes:
        folder = {"lost_pet": "pets", "lost_person": "persons", "lost_item": "items"}[case_type]
        relative = Path("data") / folder / f"{case_id}.jpg"
        absolute = BASE_DIR / relative
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_bytes(image_bytes)
        image_path = relative.as_posix()

    record = {
        "case_id": case_id,
        "case_type": case_type,
        "category": (category or "").strip().lower() or None,
        "title": title or (description or "")[:80],
        "description": description,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "date_lost": date_lost,
        "image_path": image_path,
        "status": "open",
    }
    try:
        engine.add_report(
            case_id=case_id,
            metadata=record,
            image_bytes=image_bytes,
            text=description or title,
        )
        week03_db.insert_report({**record, "source": "user"}, db_path=str(WEEK04_DB))
        specialized_index.index_ocr(
            case_id,
            " ".join(value for value in (title, description, category) if value),
        )
        if image_bytes:
            extractor = ensure_feature_extractor()
            from io import BytesIO
            from PIL import Image
            with Image.open(BytesIO(image_bytes)) as source:
                extracted = extractor.extract(source.convert("RGB"), include_clip=False)
            specialized_index.add_face(case_id, extracted.get("face_embeddings", []))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not index the report.") from exc
    return {"message": f"Report {case_id} saved and indexed.", "case": record}


def validate_image(image_bytes):
    if not image_bytes:
        return
    from io import BytesIO
    from PIL import Image
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.") from exc


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    ensure_engine()
    image_bytes = await image.read()
    validate_image(image_bytes)
    extractor = ensure_feature_extractor()
    from io import BytesIO
    from PIL import Image
    with Image.open(BytesIO(image_bytes)) as source:
        return {"features": extractor.extract(source.convert("RGB"))}


@app.post("/search")
async def search(
    image: UploadFile | None = File(None),
    text: str | None = Form(None),
    query_type: str | None = Form(None),
    category: str | None = Form(None),
    location: str | None = Form(None),
    top_k: int = Form(5),
):
    ensure_engine()
    if query_type and query_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"query_type must be one of {sorted(ALLOWED_TYPES)}")
    if not 1 <= top_k <= 50:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")
    image_bytes = await image.read() if image and image.filename else None
    validate_image(image_bytes)
    if not image_bytes and not (text and text.strip()):
        raise HTTPException(status_code=400, detail="Provide an image, text, or both.")
    if image_bytes:
        ensure_feature_extractor()
    started = time.perf_counter()
    response = pipeline.run(
        image_bytes=image_bytes,
        text=text,
        query_type=query_type,
        category=category,
        location=location,
        top_k=top_k,
    )
    return {
        "query": {"text": text, "query_type": query_type, "category": category, "location": location},
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        **response,
    }


if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str, request: Request):
        file_path = FRONTEND_DIST / path
        if path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
