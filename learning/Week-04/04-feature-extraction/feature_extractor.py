"""Combine YOLO, OCR, face recognition, and CLIP into one feature record."""

import importlib.util
import sys
from pathlib import Path

from PIL import Image


def _load_module(name, path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WEEK04 = Path(__file__).resolve().parent.parent
YOLO = _load_module("week04_yolo", WEEK04 / "01-yolo" / "detect.py")
FACES = _load_module("week04_faces", WEEK04 / "03-face" / "detect_faces.py")
FACE_EMBEDDINGS = _load_module(
    "week04_face_embeddings", WEEK04 / "03-face" / "generate_embeddings.py"
)
OCR = _load_module("week04_ocr", WEEK04 / "02-ocr" / "ocr.py")


class FeatureExtractor:
    def __init__(self, object_detector=None, ocr_extractor=None,
                 face_detector=None, face_embedder=None, clip_engine=None):
        self.object_detector = object_detector
        self.ocr_extractor = ocr_extractor
        self.face_detector = face_detector
        self.face_embedder = face_embedder
        self.clip_engine = clip_engine

    def extract(self, image, include_clip=True):
        if not isinstance(image, Image.Image):
            image = Image.open(image).convert("RGB")
        features = {
            "objects": self.object_detector.detect(image) if self.object_detector else [],
            "text": self.ocr_extractor.extract(image) if self.ocr_extractor else [],
            "ocr_text": [],
            "faces": [],
            "face_embeddings": [],
            "clip_embedding": [],
        }
        features["ocr_text"] = [
            entry.get("value", "") for entry in features["text"] if entry.get("value")
        ]
        if self.face_detector:
            detected_faces = self.face_detector.detect(image)
            features["faces"] = [{"bbox": face["bbox"]} for face in detected_faces]
            if self.face_embedder:
                for face in detected_faces:
                    try:
                        features["face_embeddings"].append(
                            self.face_embedder.embed(face["crop"]).tolist()
                        )
                    except ValueError:
                        continue
        if include_clip and self.clip_engine:
            features["clip_embedding"] = self.clip_engine._image_embedding(image).tolist()
        return features


def build_default_extractor(clip_engine=None):
    return FeatureExtractor(
        object_detector=YOLO.YOLODetector(),
        ocr_extractor=OCR.PaddleOCRExtractor(),
        face_detector=FACES.HaarFaceDetector(),
        face_embedder=FACE_EMBEDDINGS.FaceEmbedder(),
        clip_engine=clip_engine,
    )
