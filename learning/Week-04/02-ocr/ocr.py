"""Extract readable text with PaddleOCR/PP-OCR.

OCR is optional at import time and the model is created only when the
extractor is instantiated. This avoids network/model work in API startup and
lets the pipeline be tested with an injected extractor.
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(image):
    """Apply lightweight preprocessing that is safe for OCR input."""
    image = image.convert("RGB").filter(ImageFilter.SHARPEN)
    return ImageEnhance.Contrast(image).enhance(1.15)


class PaddleOCRExtractor:
    def __init__(self, ocr=None, language="en"):
        if ocr is not None:
            self.ocr = ocr
            return
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "OCR requires paddleocr and its runtime. Install requirements-week04.txt."
            ) from exc
        self.ocr = PaddleOCR(lang=language, use_doc_orientation_classify=False,
                             use_doc_unwarping=False, use_textline_orientation=False)

    def extract(self, image):
        image = preprocess_image(image)
        # PaddleOCR's current pipeline accepts paths and NumPy arrays, not PIL
        # images. Keep PIL internally for preprocessing, then cross the model
        # boundary with the supported RGB array representation.
        result = self.ocr.predict(np.asarray(image))
        entries = []
        for page in result:
            data = page.json if hasattr(page, "json") else page
            if callable(data):
                data = data()
            if isinstance(data, list):
                data = data[0] if data else {}
            data = data.get("res", data) if isinstance(data, dict) else {}
            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            boxes = data.get("rec_polys", data.get("rec_boxes", []))
            for index, value in enumerate(texts):
                entries.append({
                    "value": str(value).strip(),
                    "confidence": float(scores[index]) if index < len(scores) else 0.0,
                    "bbox": boxes[index].tolist() if index < len(boxes) and hasattr(boxes[index], "tolist") else boxes[index] if index < len(boxes) else None,
                })
        return [entry for entry in entries if entry["value"]]


def extract_text(image_path, language="en"):
    with Image.open(image_path) as image:
        return PaddleOCRExtractor(language=language).extract(image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--language", default="en")
    args = parser.parse_args()
    for item in extract_text(args.image, args.language):
        print(item)


if __name__ == "__main__":
    main()
