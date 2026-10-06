"""Generate and compare face embeddings using the optional face_recognition package."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


class FaceEmbedder:
    def __init__(self, backend=None):
        if backend is not None:
            self.backend = backend
            return
        try:
            import face_recognition
        except ImportError as exc:
            raise RuntimeError(
                "Face embeddings require face_recognition. Install requirements-week04.txt."
            ) from exc
        self.backend = face_recognition

    def embed(self, face_image):
        array = np.asarray(face_image.convert("RGB"))
        embeddings = self.backend.face_encodings(array)
        if not embeddings:
            raise ValueError("No face found in the supplied crop.")
        vector = np.asarray(embeddings[0], dtype=np.float32)
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    @staticmethod
    def similarity(first, second):
        first = np.asarray(first, dtype=np.float32)
        second = np.asarray(second, dtype=np.float32)
        denominator = np.linalg.norm(first) * np.linalg.norm(second)
        if denominator == 0:
            raise ValueError("Face embeddings must be non-zero vectors.")
        return float(np.dot(first, second) / denominator)


def embed_image(image_path):
    with Image.open(image_path) as image:
        return FaceEmbedder().embed(image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    print(embed_image(args.image).tolist())


if __name__ == "__main__":
    main()

