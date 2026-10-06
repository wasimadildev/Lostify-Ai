"""One CLIP implementation for all of Week 05, with a transformers 4/5 shim.

transformers 5 changed `CLIPModel.get_image_features` from returning a tensor to
returning a `BaseModelOutputWithPooling`. Week 05 code should not have to know
which version it is running on, so every call in this week goes through
`project()` below.

    python clip_model.py --build          # embed the whole catalog
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
DATASET_DIR = WEEK05 / "01-dataset"
MODELS_DIR = WEEK05 / "outputs" / "models"
CACHE = MODELS_DIR / "embeddings"

sys.path.insert(0, str(WEEK05 / "02-data-preparation"))
from prepare_dataset import load_cases, resolve_image  # noqa: E402

MODEL_ID = "openai/clip-vit-base-patch32"


def project(features):
    """Return the projected embedding tensor from a tensor or a model output.

    transformers <= 4 returns a plain tensor, which has no `pooler_output`, so
    one attribute check covers both versions.
    """
    pooler = getattr(features, "pooler_output", None)
    return pooler if pooler is not None else features


class ClipEncoder:
    """L2-normalised image / text embeddings from one CLIP checkpoint."""

    def __init__(self, model_id=MODEL_ID, device=None, batch_size=16):
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.torch = torch
        self.model_id = model_id
        self.batch_size = batch_size
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained(model_id).to(self.device).eval()
        self.processor = CLIPProcessor.from_pretrained(model_id)
        self.dim = int(self.model.config.projection_dim)

    def _features(self, kind, payload):
        if kind == "image":
            return self.processor(images=payload, return_tensors="pt")
        return self.processor(
            text=payload, return_tensors="pt", padding=True, truncation=True, max_length=77
        )

    def encode(self, kind, items):
        """Embed a list of images (paths/PIL) or texts. Returns float32 [N, D]."""
        torch = self.torch
        batches = []
        with torch.inference_mode():
            for start in range(0, len(items), self.batch_size):
                chunk = items[start : start + self.batch_size]
                inputs = self._features(kind, chunk)
                inputs = {key: value.to(self.device) for key, value in inputs.items()}
                getter = (
                    self.model.get_image_features
                    if kind == "image"
                    else self.model.get_text_features
                )
                vectors = project(getter(**inputs)).float()
                vectors = vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(1e-8)
                batches.append(vectors.cpu().numpy())
        return np.concatenate(batches, axis=0).astype(np.float32)

    def encode_images(self, items):
        return self.encode("image", items)

    def encode_texts(self, texts):
        return self.encode("text", texts)

    def image_paths(self):
        return [str(resolve_image(case)) for case in load_cases()]


def cosine(a, b):
    """Cosine similarity for already-normalised rows."""
    return float(np.dot(a, b))


def build_cache(model_id=MODEL_ID, force=False):
    """Embed the full catalog once and cache it as .npy + manifest."""
    CACHE.mkdir(parents=True, exist_ok=True)
    stamp = CACHE / "manifest.json"
    if stamp.exists() and not force:
        manifest = json.loads(stamp.read_text())
        if manifest.get("model_id") == model_id:
            return manifest

    encoder = ClipEncoder(model_id)
    cases = load_cases()
    started = time.perf_counter()
    embeddings = encoder.encode_images([str(resolve_image(c)) for c in cases])
    elapsed = (time.perf_counter() - started) * 1000

    np.save(CACHE / "clip_image_embeddings.npy", embeddings)
    manifest = {
        "model_id": model_id,
        "device": encoder.device,
        "dim": encoder.dim,
        "images": len(cases),
        "case_ids": [case["case_id"] for case in cases],
        "entity_ids": [case["entity_id"] for case in cases],
        "embed_ms_total": round(elapsed, 1),
        "embed_ms_per_image": round(elapsed / len(cases), 1),
    }
    stamp.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_cache():
    """(embeddings, manifest) from disk, building the cache if absent."""
    manifest = build_cache()
    embeddings = np.load(CACHE / "clip_image_embeddings.npy")
    return embeddings, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="embed the catalog")
    parser.add_argument("--force", action="store_true", help="rebuild even if cached")
    parser.add_argument("--text", nargs="*", help="embed these strings instead")
    args = parser.parse_args()

    if args.text:
        encoder = ClipEncoder()
        vectors = encoder.encode_texts(args.text)
        for text, vector in zip(args.text, vectors):
            print(f"{text!r}\n  {np.round(vector[:8], 4)} ... norm={np.linalg.norm(vector):.3f}")
        return

    manifest = build_cache(force=args.force)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()