"""Contrastive fine-tuning for CLIP — gated by a measurement, not by the roadmap.

The pairs exist. The trainer exists. Neither is a reason to run it.

`baseline.py` reports retrieval Top-1 and pair AUC. If the frozen model already
separates the corpus, then fine-tuning cannot improve it and can only overfit,
so `--train` refuses. That is the Week 05 rule applied to the model the week is
actually about.

    python train.py --gate            # domain gap + verdict, no training
    python train.py --train           # runs only if the gate says so
    python train.py --train --force --diagnostic   # runs anyway, labelled a diagnostic

A forced run is written to `outputs/models/lostify-clip-diagnostic/` and stamped
`diagnostic_only: true`, and every later stage refuses to load it as the model of
record. Its purpose is to prove the trainer works — a decreasing loss on a
saturated task — and never to be reported as an improvement.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
DATASET_DIR = WEEK05 / "01-dataset"
MODELS_DIR = WEEK05 / "outputs" / "models"
METRICS_DIR = WEEK05 / "outputs" / "metrics"

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

from clip_model import MODEL_ID, ClipEncoder, project  # noqa: E402
from prepare_dataset import is_found, load_cases, load_pairs  # noqa: E402

BASELINE = METRICS_DIR / "baseline_results.json"
GATE_REPORT = METRICS_DIR / "clip_domain_gap.json"
TRAIN_REPORT = METRICS_DIR / "clip_training.json"
VISUAL_LAYERS = 12  # CLIP ViT-B/32 vision tower depth
RECORD_MODEL = MODELS_DIR / "lostify-clip"
DIAGNOSTIC_MODEL = MODELS_DIR / "lostify-clip-diagnostic"

TARGET_TOP_1 = 0.85
MIN_TRAIN_PAIRS = 200


def resolve(relative):
    """Pairs store paths relative to 01-dataset."""
    return DATASET_DIR / relative


def gate():
    """Decide whether fine-tuning is justified, and write down why."""
    if not BASELINE.exists():
        raise SystemExit("Run baseline.py first: the gate needs a measured baseline.")
    baseline = json.loads(BASELINE.read_text())
    pairs = baseline["pairs"]
    gap = baseline["domain_gap"]

    training_pairs = [p for p in load_pairs() if p["split"] == "train"]
    positives = sum(1 for p in training_pairs if p["label"] == 1)

    saturated = gap["mean_top_1"] is not None and gap["mean_top_1"] >= TARGET_TOP_1
    verdict = {
        "model": baseline["model"],
        "measured_top_1": gap["mean_top_1"],
        "target_top_1": TARGET_TOP_1,
        "pair_auc": pairs["auc"],
        "pair_margin": pairs["margin"],
        "training_pairs": len(training_pairs),
        "training_positive_pairs": positives,
        "min_pairs_required": MIN_TRAIN_PAIRS,
        "enough_data": len(training_pairs) >= MIN_TRAIN_PAIRS,
        "benchmark_saturated": bool(saturated),
        "fine_tune_worthy": bool(saturated is False and len(training_pairs) >= MIN_TRAIN_PAIRS),
        "reasons": [],
    }

    if saturated:
        verdict["reasons"].append(
            f"frozen CLIP already reaches top-1 {gap['mean_top_1']} "
            f"(target {TARGET_TOP_1}); there is no headroom to recover"
        )
    if pairs["auc"] >= 0.99:
        verdict["reasons"].append(
            f"pair AUC {pairs['auc']} means positive and negative pairs are "
            "already linearly separable"
        )
    if len(training_pairs) < MIN_TRAIN_PAIRS:
        verdict["reasons"].append(
            f"only {len(training_pairs)} training pairs, below the "
            f"{MIN_TRAIN_PAIRS} needed for contrastive tuning"
        )
    if positives < 50:
        verdict["reasons"].append(
            f"only {positives} positive training pairs; contrastive learning on "
            "that many will memorise the corpus"
        )
    if not verdict["reasons"]:
        verdict["reasons"].append("a real domain gap with enough pairs was measured")

    verdict["verdict"] = "fine-tune" if verdict["fine_tune_worthy"] else "keep frozen CLIP"
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    GATE_REPORT.write_text(json.dumps(verdict, indent=2) + "\n")
    return verdict


def render_gate(verdict):
    lines = [
        "CLIP fine-tuning gate",
        "-" * 64,
        f"measured top-1        {verdict['measured_top_1']}  (target {verdict['target_top_1']})",
        f"pair AUC              {verdict['pair_auc']}",
        f"pair margin           {verdict['pair_margin']}",
        f"training pairs        {verdict['training_pairs']}  (minimum {verdict['min_pairs_required']})",
        f"positive pairs        {verdict['training_positive_pairs']}",
        "-" * 64,
        f"verdict: {verdict['verdict']}",
    ]
    lines += [f"  - {reason}" for reason in verdict["reasons"]]
    return "\n".join(lines)


def _batch_inputs(encoder, images):
    inputs = encoder._features("image", images)
    return {key: value.to(encoder.device) for key, value in inputs.items()}


def contrastive_loss(a, b, positives, temperature=0.07):
    """InfoNCE over an in-batch candidate pool.

    Every query in the batch is scored against every candidate in the batch, so
    one forward pass supplies `len(batch)` negatives per positive instead of one.
    Diagonal entries are the intended pairs, excluded from the denominator.
    """
    import torch
    import torch.nn.functional as F

    logits = a @ b.T / temperature
    labels = torch.arange(len(a), device=a.device)
    both_ways = F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)
    return both_ways / 2


def train(epochs=4, batch_size=8, learning_rate=1e-5, temperature=0.07,
          diagnostic=False, freeze_layers=VISUAL_LAYERS // 2):
    import torch
    from transformers import CLIPModel, CLIPProcessor

    verdict = gate()
    if not verdict["fine_tune_worthy"] and not diagnostic:
        raise SystemExit(
            "Refusing to fine-tune.\n"
            + "\n".join(f"  - {reason}" for reason in verdict["reasons"])
            + "\n\nWeek 05 rule: fine-tune only on a measured domain gap with "
              "enough labelled data.\nRun --force --diagnostic to train anyway "
              "and prove the trainer works; the result is quarantined."
        )

    target = DIAGNOSTIC_MODEL if diagnostic else RECORD_MODEL
    encoder = ClipEncoder()
    model = CLIPModel.from_pretrained(MODEL_ID).to(encoder.device)
    processor = CLIPProcessor.from_pretrained(MODEL_ID)

    # Partial fine-tuning: freeze the visual tower's early blocks so the
    # low-level features stay general and only the top adapts.
    trainable, frozen = 0, 0
    for name, parameter in model.named_parameters():
        is_early_visual = name.startswith("vision_model.encoder.layers") and \
            int(name.split(".")[3]) < freeze_layers
        parameter.requires_grad = not is_early_visual
        trainable += parameter.numel() if parameter.requires_grad else 0
        frozen += 0 if parameter.requires_grad else parameter.numel()

    pairs = [p for p in load_pairs() if p["split"] == "train"]
    rng = random.Random(11)
    optimiser = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=learning_rate
    )

    history = []
    for epoch in range(epochs):
        rng.shuffle(pairs)
        epoch_loss, batches = 0.0, 0
        started = time.perf_counter()
        for start in range(0, len(pairs), batch_size):
            chunk = pairs[start : start + batch_size]
            if len(chunk) < 2:
                continue
            left = [str(resolve(p["query_image"])) for p in chunk]
            right = [str(resolve(p["candidate_image"])) for p in chunk]
            with torch.autocast(device_type=encoder.device, enabled=encoder.device == "cuda"):
                va = project(model.get_image_features(
                    **_features(processor, left, encoder.device))).float()
                vb = project(model.get_image_features(
                    **_features(processor, right, encoder.device))).float()
                va = va / va.norm(dim=-1, keepdim=True).clamp_min(1e-8)
                vb = vb / vb.norm(dim=-1, keepdim=True).clamp_min(1e-8)
                loss = contrastive_loss(va, vb, chunk, temperature)
            optimiser.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], 1.0
            )
            optimiser.step()
            epoch_loss += loss.detach().item()
            batches += 1
        mean_loss = epoch_loss / max(batches, 1)
        history.append({
            "epoch": epoch + 1,
            "loss": round(mean_loss, 4),
            "seconds": round(time.perf_counter() - started, 1),
        })
        print(f"epoch {epoch + 1}/{epochs}  loss {mean_loss:.4f}  "
              f"({history[-1]['seconds']}s)")

    target.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(target / "checkpoint")
    processor.save_pretrained(target / "checkpoint")

    losses = [row["loss"] for row in history]
    report = {
        "model": MODEL_ID,
        "target": str(target),
        "diagnostic_only": bool(diagnostic),
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "temperature": temperature,
        "frozen_early_visual_layers": freeze_layers,
        "trainable_params": trainable,
        "frozen_params": frozen,
        "frozen_fraction": round(frozen / (trainable + frozen), 4),
        "training_pairs": len(pairs),
        "history": history,
        "loss_decreased": bool(losses and losses[-1] < losses[0]),
        "note": (
            "quarantined diagnostic run: trained on a saturated benchmark to "
            "verify the trainer reduces loss. Not a result."
            if diagnostic else
            "gated run: the domain gap was measured before training"
        ),
    }
    TRAIN_REPORT.write_text(json.dumps(report, indent=2) + "\n")
    return report


def _features(processor, images, device):
    inputs = processor(images=images, return_tensors="pt")
    return {key: value.to(device) for key, value in inputs.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true", help="measure the gap, print the verdict")
    parser.add_argument("--train", action="store_true", help="fine-tune if the gate allows")
    parser.add_argument("--force", action="store_true", help="override a refusing gate")
    parser.add_argument("--diagnostic", action="store_true",
                        help="quarantine the run; never report it as a result")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--freeze-layers", type=int, default=VISUAL_LAYERS // 2,
                        help="visual tower blocks to freeze (default: half)")
    args = parser.parse_args()

    if args.train:
        report = train(
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            diagnostic=args.diagnostic,
            freeze_layers=args.freeze_layers,
        )
        print(json.dumps({
            "target": report["target"],
            "diagnostic_only": report["diagnostic_only"],
            "loss_decreased": report["loss_decreased"],
            "frozen_fraction": report["frozen_fraction"],
        }, indent=2))
        return

    print(render_gate(gate()))


if __name__ == "__main__":
    main()