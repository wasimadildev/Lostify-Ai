"""Learned ranker: Logistic Regression and Random Forest on the fused features.

The roadmap asks for a learned ranker once enough labels exist, with a NumPy
fallback so the script still runs without scikit-learn. Missing signals are
imputed to 0.5 (neutral) plus an explicit presence mask, so the model can learn
"no face here" instead of conflating it with "face score zero".

    python learned_ranker.py

Writes outputs/metrics/learned_ranker.json.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

WEEK05 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(WEEK05 / "02-data-preparation"))

from features import CONTINUOUS, FEATURES  # noqa: E402
from fusion import roc_auc  # noqa: E402
from prepare_dataset import METRICS_DIR  # noqa: E402

REPORT = METRICS_DIR / "learned_ranker.json"
# Below this many validation positives the learned models are not fitted; the
# rule-based fusion stays the system of record.
MIN_POSITIVES = 10


def design_matrix(rows):
    """[value or 0.5 when missing] interleaved with a presence flag per feature."""
    columns = []
    for row in rows:
        values, present = [], []
        for name in CONTINUOUS:
            value = row["features"][name]
            values.append(0.5 if value is None else float(value))
            present.append(0.0 if value is None else 1.0)
        # category_match is a flag, never missing.
        values.append(float(row["features"]["category_match"]))
        present.append(1.0)
        columns.append(values + present)
    return np.asarray(columns, dtype=np.float64)


def sklearn_models():
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return None

    return {
        "logistic_regression": lambda: make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced"),
        ),
        "random_forest": lambda: RandomForestClassifier(
            n_estimators=400, min_samples_leaf=2, class_weight="balanced",
            random_state=42,
        ),
    }


class NumpyLogistic:
    """Gradient-descent logistic regression, for environments without sklearn."""

    def __init__(self, learning_rate=0.1, iterations=3000):
        self.learning_rate = learning_rate
        self.iterations = iterations

    def fit(self, x, y):
        n_features = x.shape[1]
        self.weights = np.zeros(n_features, dtype=np.float64)
        self.bias = 0.0
        for _ in range(self.iterations):
            probabilities = 1 / (1 + np.exp(-(x @ self.weights + self.bias)))
            error = probabilities - y
            self.weights -= self.learning_rate * (x.T @ error) / len(y)
            self.bias -= self.learning_rate * error.mean()
        return self

    def predict_proba(self, x):
        probabilities = 1 / (1 + np.exp(-(x @ self.weights + self.bias)))
        return np.column_stack([1 - probabilities, probabilities])


def fit_and_score(name, factory, train, valid, test):
    x_train, y_train = design_matrix(train), np.asarray(
        [r["label"] for r in train], dtype=np.float64
    )
    x_valid, y_valid = design_matrix(valid), np.asarray(
        [r["label"] for r in valid], dtype=np.float64
    )
    x_test, y_test = design_matrix(test), np.asarray(
        [r["label"] for r in test], dtype=np.float64
    )

    model = factory().fit(x_train, y_train)
    train_pred = model.predict_proba(x_train)[:, 1]
    valid_pred = model.predict_proba(x_valid)[:, 1]
    test_pred = model.predict_proba(x_test)[:, 1]
    return {
        "model": name,
        "features": len(CONTINUOUS) * 2,
        "train_auc": round(roc_auc(y_train, train_pred), 4),
        "validation_auc": round(roc_auc(y_valid, valid_pred), 4),
        "test_auc": round(roc_auc(y_test, test_pred), 4),
        "overfit": round(
            roc_auc(y_train, train_pred) - roc_auc(y_valid, valid_pred), 4
        ),
    }


def importances(name, model):
    """Feature weights, when the estimator exposes them."""
    steps = getattr(model, "steps", None)
    inner = steps[-1][1] if steps else model
    coefficients = getattr(inner, "coef_", None)
    if coefficients is not None:
        return {
            feature: round(float(value), 4)
            for feature, value in zip(
                [f"{n}" for n in CONTINUOUS]
                + [f"{n}__present" for n in CONTINUOUS] + ["category_match"],
                coefficients[0],
            )
        }
    gains = getattr(inner, "feature_importances_", None)
    if gains is not None:
        return {
            feature: round(float(value), 4)
            for feature, value in zip(
                [f"{n}" for n in CONTINUOUS]
                + [f"{n}__present" for n in CONTINUOUS] + ["category_match"],
                gains,
            )
        }
    return None


def run():
    from features import build

    rows = build()["rows"]
    by_split = {
        split: [r for r in rows if r["split"] == split]
        for split in ("train", "validation", "test")
    }
    valid_positives = sum(1 for r in by_split["validation"] if r["label"] == 1)

    factories = sklearn_models()
    backend = "scikit-learn"
    if factories is None:
        factories = {"logistic_regression_numpy": NumpyLogistic}
        backend = "numpy fallback (scikit-learn not installed)"

    results, weights = [], {}
    if valid_positives < MIN_POSITIVES:
        return {
            "backend": backend,
            "skipped": (
                f"only {valid_positives} validation positives; "
                f"{MIN_POSITIVES} required to fit a learned ranker"
            ),
            "decision": "rule-based fusion remains the system of record",
        }

    for name, factory in factories.items():
        model = factory().fit(design_matrix(by_split["train"]),
                              np.asarray([r["label"] for r in by_split["train"]],
                                         dtype=np.float64))
        results.append(fit_and_score(name, factories[name], by_split["train"],
                                     by_split["validation"], by_split["test"]))
        weights[name] = importances(name, model)

    best = max(results, key=lambda row: row["validation_auc"])
    return {
        "backend": backend,
        "min_positives_required": MIN_POSITIVES,
        "validation_positives": valid_positives,
        "models": results,
        "selected_by_validation": best["model"],
        "test_auc": best["test_auc"],
        "clip_only_test_auc": round(roc_auc(
            [r["label"] for r in by_split["test"]],
            [r["features"]["clip_score"] for r in by_split["test"]],
        ), 4),
        "weights": weights,
        "decision": (
            "the learned ranker is kept only if it beats CLIP alone on the "
            "untouched test split"
        ),
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    result = run()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")

    if "skipped" in result:
        print(f"learned ranker skipped: {result['skipped']}")
        print(f"decision: {result['decision']}")
        return
    print(f"Learned ranker ({result['backend']})")
    print("-" * 78)
    print(f"{'model':>26}{'train':>9}{'valid':>9}{'test':>9}{'overfit':>10}")
    for row in result["models"]:
        print(f"{row['model']:>26}{row['train_auc']:>9.4f}{row['validation_auc']:>9.4f}"
              f"{row['test_auc']:>9.4f}{row['overfit']:>10.4f}")
    print("-" * 78)
    print(f"clip-only test AUC {result['clip_only_test_auc']:.4f}")
    print(f"selected by validation: {result['selected_by_validation']} "
          f"(test {result['test_auc']:.4f})")
    print(f"decision: {result['decision']}")


if __name__ == "__main__":
    main()