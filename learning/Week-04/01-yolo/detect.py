"""Run YOLO object detection on an image.

The Ultralytics import is intentionally lazy so this module can be imported
for tests and documentation without downloading model weights.
"""

import argparse
from pathlib import Path

from PIL import Image

from visualize import draw_detections

DEFAULT_MODEL = "yolo11n.pt"


class YOLODetector:
    def __init__(self, model_name=DEFAULT_MODEL, model=None, confidence=0.25):
        self.confidence = confidence
        if model is not None:
            self.model = model
            return
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "YOLO requires ultralytics. Install requirements-week04.txt."
            ) from exc
        self.model = YOLO(model_name)

    def detect(self, image, classes=None):
        """Return JSON-serializable detections for a PIL image or image path."""
        results = self.model.predict(
            source=image,
            conf=self.confidence,
            classes=classes,
            verbose=False,
        )
        detections = []
        for result in results:
            names = result.names
            boxes = result.boxes
            for box, confidence, class_id in zip(
                boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist()
            ):
                index = int(class_id)
                detections.append({
                    "class": names[index],
                    "class_id": index,
                    "confidence": float(confidence),
                    "bbox": [float(value) for value in box],
                })
        return detections


def detect_image(image_path, output_path=None, model_name=DEFAULT_MODEL):
    image = Image.open(image_path).convert("RGB")
    detections = YOLODetector(model_name=model_name).detect(image)
    if output_path:
        draw_detections(image, detections, output_path)
    return detections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/annotated.jpg"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    detections = detect_image(args.image, args.output, args.model)
    for detection in detections:
        print(detection)
    print(f"Annotated image written to {args.output}")


if __name__ == "__main__":
    main()

