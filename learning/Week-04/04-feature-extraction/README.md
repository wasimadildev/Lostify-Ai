# Unified feature extraction

`feature_extractor.py` combines object detections, OCR entries, face boxes,
face embeddings, and an optional CLIP embedding into one JSON-serializable
feature record. Components are injectable for tests and alternative models.

