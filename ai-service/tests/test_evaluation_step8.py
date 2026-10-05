"""Upgrade step 8 tests: frozen-test metric math, comparison gating and a real
end-to-end train->manifest->frozen-evaluation pass on trivially separable data."""
import os
import sys
import tempfile

os.makedirs("/home/user/.tmp", exist_ok=True)

STORE = tempfile.mkdtemp(prefix="cs-ms8-", dir="/home/user/.tmp")
os.environ["MODEL_STORE"] = STORE
os.environ.setdefault("DINOV2_ENABLED", "false")
os.environ["STRICT_20_CLASS_TRAINING"] = "false"   # dev experiment with 3 classes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from app.evaluation import compare_reports, compute_classification_metrics

CLASSES = ["a", "b"]


def test_metrics_perfect():
    probs = np.array([[0.9, 0.1], [0.8, 0.2], [0.1, 0.9], [0.2, 0.8]])
    m = compute_classification_metrics(["a", "a", "b", "b"], probs, CLASSES)
    assert m["accuracy"] == 1.0 and m["macro_f1"] == 1.0 and m["mean_ap"] == 1.0
    assert m["detection_map50"] is None  # detector metrics wired but honest-null


def test_metrics_known_confusion():
    # preds: a,a,a,b  -> b recall 0.5, a precision 2/3
    probs = np.array([[0.7, 0.3], [0.6, 0.4], [0.55, 0.45], [0.3, 0.7]])
    m = compute_classification_metrics(["a", "a", "b", "b"], probs, CLASSES)
    assert m["accuracy"] == 0.75
    pc = m["per_class"]
    assert pc["a"]["recall"] == 1.0 and round(pc["a"]["precision"], 4) == round(2 / 3, 4)
    assert pc["b"]["recall"] == 0.5
    assert m["confusion_matrix"]["b"]["a"] == 1


def test_compare_rules():
    base = {"n": 10, "accuracy": 0.8, "macro_f1": 0.8,
            "per_class": {"a": {"recall": 0.9}, "b": {"recall": 0.7}}}
    assert compare_reports(None, {"n": 0})["recommendation"] == "reject"
    assert compare_reports(None, base)["recommendation"] == "deploy"

    better = {"n": 10, "accuracy": 0.9, "macro_f1": 0.9,
              "per_class": {"a": {"recall": 0.95}, "b": {"recall": 0.85}}}
    assert compare_reports(base, better)["recommendation"] == "deploy"

    worse_important = {"n": 10, "accuracy": 0.95, "macro_f1": 0.95,
                       "per_class": {"a": {"recall": 0.99}, "b": {"recall": 0.5}}}
    out = compare_reports(base, worse_important, max_drop=0.05)
    assert out["recommendation"] == "reject"          # better overall, worse on b

    slightly_worse = {"n": 10, "accuracy": 0.7, "macro_f1": 0.7,
                      "per_class": {"a": {"recall": 0.9}, "b": {"recall": 0.7}}}
    assert compare_reports(base, slightly_worse)["recommendation"] == "manual_review"


def test_end_to_end_train_and_frozen_eval(tmp_path):
    from app.datasets import build_dataset
    from app.evaluation import evaluate_checkpoint
    from app.ml import train_classifier
    from app.model_registry import version_meta

    rng = np.random.default_rng(0)
    records = []
    colors = {"citrus-psyllid": (150, 60, 60), "citrus-leaf-miner": (60, 150, 60), "no-citrus-pest": (60, 60, 150)}
    for cls, col in colors.items():
        for i in range(6):
            arr = np.zeros((64, 64, 3), np.uint8)
            arr[:] = col
            arr = arr + rng.integers(0, 25, arr.shape).astype(np.uint8)
            p = tmp_path / f"{cls}-{i}.png"
            Image.fromarray(arr).save(p)
            records.append({"image_id": p.stem, "image_path": str(p), "pest_id": cls})

    manifest = build_dataset(records, "dataset-eval-v1", test_fraction=0.34)
    train_ids = [r for r in records if manifest["splits"][r["image_id"]] in ("train", "val")]

    result = train_classifier({
        "dataset_version": "dataset-eval-v1", "base_model": "resnet18",
        "epochs": 30, "batch_size": 4, "learning_rate": 3e-3, "image_size": 64,
        "classes": [{"id": k, "name": k} for k in colors],
        "training_records": train_ids,
    })
    assert result["status"] == "completed", result.get("metrics")
    meta = version_meta(result["version"])

    report = evaluate_checkpoint(meta, records, manifest)
    assert report["frozen_test"] is True
    assert report["n_test"] >= 2 and report["skipped"] == 0
    assert report["accuracy"] >= 0.8          # separable solid colors
    assert report["latency_ms_per_image"] is not None
    assert set(report["per_class"]) == set(colors)
    # frozen test ids were never trained on
    train_set = {r["image_id"] for r in train_ids}
    assert not (set(manifest["frozen_test_ids"]) & train_set)
