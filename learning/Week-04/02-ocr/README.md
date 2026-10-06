# OCR

`ocr.py` preprocesses an image and extracts text, confidence, and bounding
boxes through PaddleOCR/PP-OCR. OCR is loaded lazily because model weights are
large and downloaded only when the extractor is used.

