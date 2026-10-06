"""Face detection and cropping with OpenCV's built-in Haar detector."""

from pathlib import Path

import numpy as np
from PIL import Image


class HaarFaceDetector:
    def __init__(self, classifier=None, scale_factor=1.1, min_neighbors=5):
        if classifier is None:
            try:
                import cv2
            except ImportError as exc:
                raise RuntimeError("Face detection requires opencv-python.") from exc
            classifier = cv2.CascadeClassifier(
                str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
            )
        self.classifier = classifier
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors

    def detect(self, image):
        import cv2
        rgb = np.asarray(image.convert("RGB"))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        boxes = self.classifier.detectMultiScale(
            gray, scaleFactor=self.scale_factor, minNeighbors=self.min_neighbors
        )
        faces = []
        for x, y, width, height in boxes:
            faces.append({
                "bbox": [int(x), int(y), int(x + width), int(y + height)],
                "crop": image.crop((x, y, x + width, y + height)),
            })
        return faces

