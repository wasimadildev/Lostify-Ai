# 04-clip — baseline, a refusal, and proof the refusal was correct

## The result

Frozen CLIP already solves this corpus. There is no domain gap, so Week 05
does not fine-tune it.

```text
arm                       top1    top5     MRR  pairs AUC     ms/q  record
frozen                   1.000   1.000   1.000     0.9987    0.039  yes
diagnostic_finetuned     0.826   1.000   0.899     0.9899    0.187  NO (quarantined)
diagnostic deltas: top_1 -0.1739, mrr -0.1014, pairs_auc -0.0088, ms/q +0.148
```

Retrieval is 46 lost queries against 46 found candidates, 512-d embeddings,
44.8 ms per image to embed, exact cosine search. Every lost report retrieves
its own found report at rank 1.

## Files

| File | Purpose |
| --- | --- |
| `clip_model.py` | Shared encoder. L2-normalised image/text embeddings + cache. |
| `baseline.py` | The frozen baseline: retrieval, pairs, latency, domain gap. |
| `train.py` | InfoNCE trainer behind a gate that refuses on a saturated benchmark. |
| `evaluate.py` | Which checkpoint is the model of record, and what training did. |
| `verify_faiss.py` | FAISS-vs-NumPy agreement, in a torch-free process. |

## Why fine-tuning was refused

```bash
python train.py --gate
```

```text
measured top-1        1.0  (target 0.85)
pair AUC              0.9987
training pairs        96  (minimum 200)
positive pairs        32
verdict: keep frozen CLIP
  - frozen CLIP already reaches top-1 1.0 (target 0.85); no headroom to recover
  - pair AUC 0.9987 means positive and negative pairs are already separable
  - only 96 training pairs, below the 200 needed for contrastive tuning
  - only 32 positive training pairs; contrastive learning will memorise the corpus
```

## "We didn't train it" is not the same as "our trainer is broken"

That distinction matters, so it is measured. A forced run trains on the same
pairs and quarantines itself in `outputs/models/lostify-clip-diagnostic/`, stamped
`diagnostic_only: true`; `evaluate.py` refuses to treat it as the model of
record.

```bash
python train.py --train --force --diagnostic --epochs 4
```

```text
epoch 1/4  loss 1.8909
epoch 2/4  loss 1.4163
epoch 3/4  loss 1.1895
epoch 4/4  loss 0.9649     loss decreased: true
frozen visual layers: 6 of 12 (28.1% of parameters frozen)
```

The trainer optimises fine. The benchmark then gets **worse**: top-1 falls from
1.000 to 0.826 and search cost rises 4.8×. That is textbook overfitting — 32
positive pairs, each a deterministic transform of its own source image — and it
is the empirical confirmation that refusing was correct rather than convenient.

## The uncomfortable part: the benchmark is too easy

Top-1 = 1.000 is not evidence that Lostify works. It is evidence that the test
is trivial. Positive pairs average cosine **0.9104** and negatives **0.5459** —
near-duplicate territory, because each "found" view is a deterministic transform
of the lost photo it belongs to.

The one number here that looks like a real-world measurement is the novel-item
protocol, which queries unseen lost reports against an index that deliberately
excludes their true found view:

```text
novel/validation   false-match 14.3% at threshold 0.8655
novel/test         false-match  0.0% at threshold 0.8655
```

Accepting a match above `positive_mean - positive_std` = 0.8655, one in seven
unseen validation items would be attached to an unrelated candidate. Real second
captures are the missing ingredient; see the limitations section of the
Week 05 README.

## FAISS

```bash
python verify_faiss.py
```

faiss and torch each ship an OpenMP runtime and importing both into one process
aborts with `OMP: Error #15`. Evaluation therefore uses exact NumPy cosine
search — for a 46-candidate index that is both exact and faster than any
approximate index — and `verify_faiss.py` exercises the FAISS path in a
torch-free subprocess, which is how the serving layer runs it.