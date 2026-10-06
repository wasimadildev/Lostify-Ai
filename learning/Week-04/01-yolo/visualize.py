"""Draw detection boxes without requiring a deep-learning runtime."""

from pathlib import Path
from typing import Iterable, Mapping

from PIL import Image, ImageDraw


def draw_detections(image, detections: Iterable[Mapping], output_path=None):
    """Draw ``bbox``, ``class`` and ``confidence`` fields on a PIL image."""
    canvas = image.copy().convert("RGB")
    draw = ImageDraw.Draw(canvas)
    for detection in detections:
        x1, y1, x2, y2 = (int(value) for value in detection["bbox"])
        label = f'{detection["class"]} {float(detection["confidence"]):.2f}'
        draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
        draw.text((x1 + 2, max(0, y1 - 16)), label, fill="red")
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path)
    return canvas

