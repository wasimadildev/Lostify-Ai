# 03-yolo — object detection, and an honest decision about fine-tuning

## The rule this stage enforces

The Week 05 README says it plainly:

> Fine-tune YOLO **only if** the Lostify detection classes require it. Do not
> fine-tune just because it is on the roadmap.

So `train.py` measures the domain gap first and **refuses to train** when
training is not justified. It is a gate, not a suggestion.

## Files

| File | Purpose |
| --- | --- |
| `dataset.yaml` | 4-class Lostify config: `phone`, `wallet`, `bag`, `laptop`. |
| `train.py` | `--gap` measure · `--export` build dataset · `--train` fine-tune (gated). |
| `validate.py` | Pretrained **vs** fine-tuned: P, R, mAP50, mAP50-95, latency. |
| `inference.py` | Detections, and the `object_score` the ranker consumes. |
| `stability.py` | Does the detector survive the augmentation? Measured, not assumed. |

## The domain-gap gate

```bash
python train.py --gap
```

For every `ITEM` / `VEHICLE` case it runs the COCO-pretrained detector and asks
a narrow question: *did it fire a box whose class actually means something for
this Lostify category?* A phone case counts as covered only if the detector
found `cell phone` / `remote` / `mouse`.

```text
overall coverage = covered item-like cases / total item-like cases
verdict          = fine-tune  if coverage < 0.60 AND real annotations exist
                 = keep pretrained otherwise
```

## Why the gate currently says "keep pretrained"

Two independent reasons, both written to `outputs/metrics/yolo_domain_gap.json`
rather than left as a claim:

1. **The pretrained detector largely works on this corpus.** Wallet, phone,
   laptop, umbrella, bottle and bicycle are all COCO classes, so the headroom
   for fine-tuning on 46 subjects is small.
2. **There are no ground-truth boxes.** The Week 04 corpus ships photographs,
   not annotations. Pseudo-labelling with the pretrained detector and then
   fine-tuning on that output can at best preserve the teacher's behaviour —
   self-distillation, not learning.

To train for real, label boxes into `01-dataset/annotations.json`:

```json
{
  "annotations": {
    "ITEMS-10": [
      {"class": "phone", "bbox": [x1, y1, x2, y2], "confidence": 1.0}
    ]
  }
}
```

Then `--export` records `label_source: "annotations.json"` and `train.py` will
run once coverage is low *and* every class has at least 25 boxes.

```bash
python train.py --gap
python train.py --export
python train.py --train --epochs 20 --imgsz 320 --batch 8
python validate.py
```

## `object_score` for re-ranking

Detection lists cannot be compared directly, so each image is reduced to a
multiset of detected classes and scored with Jaccard overlap:

```text
query     = {cell phone: 1}
candidate = {cell phone: 1, handbag: 1}      → 1/2 = 0.5
query     = {}  candidate = {cell phone: 1}   → 0.0   (empty is "no evidence")
```

Two empty detections deliberately score `0.0` rather than `1.0`: "neither image
contains a recognisable object" is missing evidence, not a match.

```bash
python inference.py PETS-01
python inference.py PETS-01 --against FOUND-PETS-01
```

## Measured: how much object evidence survives the augmentation

Before weighting `object_score` in the ranker, the obvious question is whether
it is stable across the lost → found transformation at all. Measured:

```bash
python stability.py
```

```text
lost images with a detection                40/46   87.0%
found views with a detection                37/46   80.4%
detections retained by augmentation         92.5%
true pairs, identical object score          23/46   50.0%
mean object_score on true pairs              0.618
breakdown: agree 23, disagree 13, found blank 4, lost blank 1, both blank 5
```

The first result is good news, and it corrects an assumption worth stating: the
augmentation is **not** destructive. 92.5% of the objects detected in the lost
photo are still detected in its own "found" view. Translation, crop, flip,
rotate and JPEG are survivable for this detector.

The second result is the one that matters for the ranker: on true pairs the
object evidence is **identical only half the time**, and a fifth of pairs
disagree outright. So `object_score` cannot rank on its own. It stays in the
ranker as a *low-weight* feature, not as a gate — and section 07 reports the
ablation that measures exactly what it is worth.

Note that these figures are only reproducible if the found/lost split is taken
from `status`, not from `type`. `type` has six values (`found_item`,
`found_pet`, `found_person` plus their `lost_` counterparts), so filtering on
`type == "found_item"` silently drops two thirds of the corpus and inflates the
damage. `prepare_dataset.is_found()` exists for exactly this reason.

The lesson for the week: CLIP is the backbone and the object detector is
corroborating evidence, because CLIP separates this corpus almost perfectly and
the detector separates it about half as well.