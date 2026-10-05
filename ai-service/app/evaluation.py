"""Frozen-test evaluation + model comparison gating (upgrade step 8).

Every candidate model is evaluated on the FROZEN test split of a dataset
version - never on its own training/val images. Deployment (step 7 governance)
requires a frozen_eval in the model's metrics, and when a production model
exists, a comparison whose recommendation is 'deploy'.

mAP50 / mAP50-95 (IoU-based) belong to the *detector* stage; they are wired as
explicit fields here and stay null until a YOLO checkpoint with bounding boxes
is registered - classification quality uses probability-based per-class AP.
Nothing is fabricated.
"""
from __future__ import annotations

import os
import time

import numpy as np
from PIL import Image

try:
    import torch
    from torchvision import transforms
except Exception:  # pragma: no cover
    torch = None
    transforms = None

try:
    from sklearn.metrics import average_precision_score
except Exception:  # pragma: no cover
    average_precision_score = None


def compute_classification_metrics(y_true: list[str], y_prob: np.ndarray,
                                   classes: list[str]) -> dict:
    """Pure metric math - unit-testable without torch."""
    n = len(y_true)
    if n == 0 or len(y_prob) == 0:
        return {"n": 0}
    preds = [classes[int(i)] for i in np.argmax(y_prob, axis=1)]
    correct = sum(1 for t, p in zip(y_true, preds) if t == p)
    accuracy = correct / n

    per_class = {}
    confusion = {t: {p: 0 for p in classes} for t in classes}
    for t, p in zip(y_true, preds):
        confusion[t][p] += 1
    for c in classes:
        tp = confusion[c][c]
        fp = sum(confusion[t][c] for t in classes if t != c)
        fn = sum(confusion[c][p] for p in classes if p != c)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        idx = classes.index(c)
        ap = None
        if average_precision_score is not None:
            truth = np.array([1 if t == c else 0 for t in y_true])
            if truth.sum() > 0 and (truth == 0).sum() > 0:
                ap = float(average_precision_score(truth, y_prob[:, idx]))
        per_class[c] = {"precision": round(precision, 4), "recall": round(recall, 4),
                        "f1": round(f1, 4), "ap": round(ap, 4) if ap is not None else None}

    macros = {k: float(np.mean([v[k] for v in per_class.values()]))
              for k in ("precision", "recall", "f1")}
    aps = [v["ap"] for v in per_class.values() if v["ap"] is not None]
    return {
        "n": n,
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macros["precision"], 4),
        "macro_recall": round(macros["recall"], 4),
        "macro_f1": round(macros["f1"], 4),
        "mean_ap": round(float(np.mean(aps)), 4) if aps else None,
        "per_class": per_class,
        "confusion_matrix": confusion,
        # Detector-stage metrics; populated once a trained YOLO is evaluated.
        "detection_map50": None,
        "detection_map50_95": None,
    }


def _load_checkpoint(version_meta: dict):
    from .ml import create_model
    ckpt = version_meta.get("checkpoint_path")
    data = torch.load(ckpt, map_location="cpu", weights_only=False)
    classes = [c["id"] for c in data["classes"]]
    model, _ = create_model(data.get("architecture", "mobilenet_v3_small"), len(classes))
    model.load_state_dict(data["model_state"])
    model.eval()
    return model, classes, int(data.get("image_size", 224))


def evaluate_checkpoint(version_meta: dict, records: list[dict],
                        manifest: dict, max_images: int | None = None) -> dict:
    """Run a registered checkpoint over the manifest's frozen test split."""
    if torch is None:
        raise RuntimeError("PyTorch not installed")
    model, classes, image_size = _load_checkpoint(version_meta)
    test_ids = set(manifest.get("frozen_test_ids") or [])
    splits = manifest.get("splits") or {}
    by_id = {str(r.get("image_id") or r.get("id")): r for r in records}
    rows = [by_id[i] for i in test_ids if i in by_id]
    if max_images:
        rows = rows[: max(1, int(max_images))]

    tf = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    device = torch.device("cpu")
    y_true, probs = [], []
    skipped = 0
    # warm-up so latency numbers are honest
    dummy = torch.randn(1, 3, image_size, image_size)
    with torch.no_grad():
        model(dummy)
    t0 = time.perf_counter()
    with torch.no_grad():
        for r in rows:
            label = r.get("pest_id")
            path = r.get("image_path")
            if label not in classes or not path or not os.path.exists(path):
                skipped += 1
                continue
            try:
                img = Image.open(path).convert("RGB")
            except Exception:
                skipped += 1
                continue
            x = tf(img).unsqueeze(0).to(device)
            p = torch.softmax(model(x), dim=1)[0].cpu().numpy()
            y_true.append(label)
            probs.append(p)
    seconds = time.perf_counter() - t0
    metrics = compute_classification_metrics(y_true, np.stack(probs) if probs else np.zeros((0, len(classes))), classes)
    metrics.update({
        "model_version": version_meta.get("version"),
        "dataset_version": manifest.get("version"),
        "frozen_test": True,
        "n_test": len(y_true),
        "skipped": skipped,
        "latency_ms_per_image": round(1000 * seconds / len(y_true), 1) if y_true else None,
        "device": "cpu",
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    return metrics


def compare_reports(current: dict | None, candidate: dict,
                    important_classes: list[str] | None = None,
                    max_drop: float | None = None, eps: float | None = None) -> dict:
    """Recommendation gate. A candidate that is better overall but worse on an
    important pest must NOT auto-replace production."""
    max_drop = float(os.getenv("COMPARE_MAX_DROP", "0.05")) if max_drop is None else max_drop
    eps = float(os.getenv("COMPARE_EPS", "0.01")) if eps is None else eps
    if not candidate or candidate.get("n", 0) == 0:
        return {"recommendation": "reject", "reasons": ["Candidate has no frozen-test results."]}
    if current is None or current.get("n", 0) == 0:
        return {"recommendation": "deploy",
                "reasons": ["No current production model with frozen results; candidate evaluated on frozen test set."]}
    reasons = []
    verdict = "deploy"
    if candidate.get("accuracy", 0) < current.get("accuracy", 0) - eps:
        verdict = "manual_review"
        reasons.append(f"accuracy {candidate.get('accuracy')} < current {current.get('accuracy')} - {eps}")
    if candidate.get("macro_f1", 0) < current.get("macro_f1", 0) - eps:
        verdict = "manual_review"
        reasons.append(f"macro_f1 {candidate.get('macro_f1')} < current {current.get('macro_f1')} - {eps}")
    important = important_classes or sorted((current.get("per_class") or {}).keys())
    for c in important:
        cur_r = (current.get("per_class") or {}).get(c, {}).get("recall")
        can_r = (candidate.get("per_class") or {}).get(c, {}).get("recall")
        if cur_r is None or can_r is None:
            continue
        if can_r < cur_r - max_drop:
            verdict = "reject"
            reasons.append(f"important class {c}: recall {can_r} vs current {cur_r} (drop > {max_drop})")
    if not reasons:
        reasons.append("Candidate meets or beats the current production model on the frozen test set.")
    return {"recommendation": verdict, "reasons": reasons,
            "current": {"accuracy": current.get("accuracy"), "macro_f1": current.get("macro_f1")},
            "candidate": {"accuracy": candidate.get("accuracy"), "macro_f1": candidate.get("macro_f1")}}
