"""Which CLIP checkpoint is the model of record, and did anything improve?

The answer this week is "the frozen one", and the job of this script is to make
that a measurement rather than an assertion:

* evaluate the model of record (frozen CLIP) under the same protocol as
  `baseline.py`, so the two files are directly comparable;
* if a quarantined diagnostic checkpoint exists, evaluate it too and report the
  delta — not to adopt it, but to show what fine-tuning on a saturated
  benchmark actually did;
* if a gate-passed checkpoint ever exists, evaluate that instead.

    python evaluate.py

Writes outputs/metrics/improved_clip_results.json.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-data-preparation"))

import baseline as baseline_module  # noqa: E402
from clip_model import MODEL_ID, ClipEncoder, project  # noqa: E402
from prepare_dataset import (  # noqa: E402
    METRICS_DIR, TEST, VALIDATION, is_found, load_cases, load_split,
)

REPORT = METRICS_DIR / "improved_clip_results.json"
BASELINE = METRICS_DIR / "baseline_results.json"
DIAGNOSTIC = Path(__file__).resolve().parent.parent / "outputs" / "models" / "lostify-clip-diagnostic" / "checkpoint"


def embed_with_checkpoint(checkpoint, cases):
    """Embed the catalog with a fine-tuned checkpoint instead of the hub model."""
    import torch
    from transformers import CLIPModel, CLIPProcessor

    from prepare_dataset import resolve_image

    encoder = ClipEncoder()
    model = CLIPModel.from_pretrained(checkpoint).to(encoder.device).eval()
    processor = CLIPProcessor.from_pretrained(checkpoint)
    started = time.perf_counter()
    paths = [str(resolve_image(case)) for case in cases]
    outputs = []
    with torch.inference_mode():
        for start in range(0, len(paths), encoder.batch_size):
            chunk = paths[start : start + encoder.batch_size]
            inputs = processor(images=chunk, return_tensors="pt")
            inputs = {key: value.to(encoder.device) for key, value in inputs.items()}
            vectors = project(model.get_image_features(**inputs)).float()
            vectors = vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(1e-8)
            outputs.append(vectors.cpu().numpy())
    elapsed = (time.perf_counter() - started) * 1000
    return (
        np.concatenate(outputs, axis=0).astype(np.float32),
        {"embed_ms_per_image": round(elapsed / len(paths), 1)},
    )


def evaluate_arm(name, embeddings, manifest, cases, diagnostic_only=False, checkpoint=None):
    found = [c for c in cases if is_found(c)]
    lost = [c for c in cases if not is_found(c)]

    arm = baseline_module.evaluate_protocol("catalog", lost, found, embeddings, manifest)
    catalog = dict(arm)
    arm["checkpoint"] = str(checkpoint) if checkpoint else MODEL_ID
    arm["diagnostic_only"] = diagnostic_only
    arm["model_of_record"] = not diagnostic_only

    for split in (VALIDATION, TEST):
        split_cases = load_split(split)
        key = f"per_split/{split}"
        arm[key] = baseline_module.evaluate_protocol(
            key,
            [c for c in split_cases if not is_found(c)],
            [c for c in split_cases if is_found(c)],
            embeddings,
            manifest,
        )

    arm["headline"] = {
        "top_1": catalog.get("top_1"),
        "top_5": catalog.get("top_5"),
        "mrr": catalog.get("mrr"),
        "pairs_auc": baseline_module.evaluate_pairs(embeddings, manifest)["auc"],
        "search_ms_per_query": catalog.get("search_ms_per_query"),
    }
    return arm


def run():
    if not BASELINE.exists():
        raise SystemExit("Run baseline.py first: this script compares against it.")
    frozen = json.loads(BASELINE.read_text())
    cases = load_cases()

    _, manifest = baseline_module.load_cache()
    baseline_manifest = {
        "case_ids": [c["case_id"] for c in cases],
        "entity_ids": [c["entity_id"] for c in cases],
        "dim": frozen["dim"],
    }

    from clip_model import load_cache

    frozen_embeddings, _ = load_cache()
    arms = {
        "frozen": evaluate_arm("frozen", frozen_embeddings, baseline_manifest, cases)
    }

    if DIAGNOSTIC.exists():
        fine_embeddings, fine_meta = embed_with_checkpoint(DIAGNOSTIC, cases)
        arms["diagnostic_finetuned"] = evaluate_arm(
            "diagnostic_finetuned",
            fine_embeddings,
            {**baseline_manifest, **fine_meta},
            cases,
            diagnostic_only=True,
            checkpoint=DIAGNOSTIC,
        )

    base_head = arms["frozen"]["headline"]
    result = {
        "decision": "adopt frozen CLIP",
        "model_of_record": MODEL_ID,
        "reason": (
            "the frozen baseline already reaches "
            f"top-1 {base_head['top_1']} with pair AUC {base_head['pairs_auc']}; "
            "the fine-tuning gate refused to train a model of record"
        ),
        "arms": arms,
        "deltas": {},
    }

    diagnostic = arms.get("diagnostic_finetuned")
    if diagnostic:
        for metric in ("top_1", "top_5", "mrr", "pairs_auc", "search_ms_per_query"):
            before, after = base_head[metric], diagnostic["headline"][metric]
            result["deltas"][metric] = (
                round(after - before, 4) if None not in (before, after) else None
            )
        top1_delta = result["deltas"]["top_1"]
        result["diagnostic_verdict"] = (
            f"fine-tuning changed top-1 by {top1_delta:+}; a saturated benchmark "
            "cannot show an improvement, and the checkpoint stays quarantined"
            if top1_delta is not None else
            "fine-tuning produced no comparable top-1; the checkpoint stays "
            "quarantined"
        )

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    return result


def render(result):
    lines = [
        "CLIP evaluation",
        "-" * 74,
        f"{'arm':<22}{'top1':>8}{'top5':>8}{'MRR':>8}{'pairs AUC':>11}{'ms/q':>9}  record",
    ]
    lines.append("-" * 84)
    for name, arm in result["arms"].items():
        head = arm["headline"]
        lines.append(
            f"{name:<22}{head['top_1']:>8.3f}{head['top_5']:>8.3f}"
            f"{head['mrr']:>8.3f}{head['pairs_auc']:>11.4f}"
            f"{head['search_ms_per_query']:>9.3f}"
            f"  {'yes' if arm['model_of_record'] else 'NO (quarantined)'}"
        )
    lines += ["-" * 84, f"decision: {result['decision']}", f"reason  : {result['reason']}"]
    if result.get("deltas"):
        deltas = ", ".join(f"{k} {v:+}" for k, v in result["deltas"].items() if v is not None)
        lines.append(f"diagnostic deltas: {deltas}")
        lines.append(f"diagnostic note  : {result['diagnostic_verdict']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(run()))