"""Bootstrap YOLO11 detection training (upgrade step 9).

Verified CLASSIFICATION images are converted into a YOLO detection dataset with
full-image bounding boxes. These are explicitly BOOTSTRAP-quality annotations
(they localise "somewhere in this image", not a precise box) - real box
annotations from experts replace them over time. The frozen test split is kept
separate, exactly as for classification datasets.
"""
from __future__ import annotations

import json
import os
import random
import shutil
import time
from pathlib import Path

from .model_registry import DEFAULT_CLASSES, register_model

CLASS_IDS = [c["id"] for c in DEFAULT_CLASSES]
CLASS_TO_IDX = {cid: i for i, cid in enumerate(CLASS_IDS)}

MODEL_STORE = os.getenv("MODEL_STORE", "/app/model-store")


def build_yolo_dataset(records: list[dict], out_dir: str,
                       splits: dict | None = None, seed: int = 42) -> dict:
    """Write an ultralytics-ready dataset: images/<split>/, labels/<split>/,
    dataset.yaml. Returns stats."""
    out = Path(out_dir)
    stats = {"written": 0, "skipped": 0, "per_split": {}, "classes": CLASS_IDS}
    rng = random.Random(seed)
    for split in ("train", "val", "test"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    for rec in records:
        pid = rec.get("pest_id")
        path = rec.get("image_path")
        if pid not in CLASS_TO_IDX or not path or not Path(path).exists():
            stats["skipped"] += 1
            continue
        split = (splits or {}).get(str(rec.get("image_id") or rec.get("id")))
        if split not in ("train", "val", "test"):
            split = "train" if rng.random() < 0.8 else "val"   # manifest-less fallback
        stem = f"{split}-{pid}-{Path(path).stem}"
        shutil.copyfile(path, out / "images" / split / f"{stem}.jpg")
        # bootstrap label: single full-image box
        (out / "labels" / split / f"{stem}.txt").write_text(
            f"{CLASS_TO_IDX[pid]} 0.5 0.5 1.0 1.0\n", encoding="utf-8")
        stats["written"] += 1
        stats["per_split"][split] = stats["per_split"].get(split, 0) + 1

    yaml_lines = [
        f"path: {out.resolve()}",
        "train: images/train",
        "val: images/val",
    ]
    if stats["per_split"].get("test"):
        yaml_lines.append("test: images/test")
    yaml_lines.append("names:")
    yaml_lines += [f"  {i}: {cid}" for i, cid in enumerate(CLASS_IDS)]
    yaml_lines.append("# bootstrap_labels: full-image boxes derived from verified")
    yaml_lines.append("# classification images; replace with expert boxes over time.")
    (out / "dataset.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    return stats


def train_yolo(payload: dict) -> dict:
    """Train YOLO11s on a bootstrap dataset. Never activates production."""
    try:
        from ultralytics import YOLO
    except Exception as exc:
        return {"status": "failed", "error": f"ultralytics unavailable: {exc}"}
    dataset_version = payload.get("dataset_version") or time.strftime("%Y%m%d")
    out_dir = payload.get("out_dir") or str(Path(MODEL_STORE) / "yolo" / dataset_version)
    stats = build_yolo_dataset(payload.get("records") or [], out_dir,
                               splits=payload.get("splits"))
    if stats["written"] < 4 or not stats["per_split"].get("train"):
        return {"status": "needs_more_data", "stats": stats}

    epochs = max(1, min(int(payload.get("epochs", 10)), 100))
    imgsz = int(payload.get("imgsz", 640))
    base = payload.get("base_model", "yolo11s.pt")
    model = YOLO(base)
    t0 = time.time()
    results = model.train(data=str(Path(out_dir) / "dataset.yaml"), epochs=epochs,
                          imgsz=imgsz, batch=int(payload.get("batch", 4)),
                          device=payload.get("device", "cpu"), workers=0,
                          project=str(Path(MODEL_STORE) / "yolo-runs"),
                          name=dataset_version, exist_ok=True, verbose=False)
    metrics = {"epochs": epochs, "imgsz": imgsz, "duration_seconds": round(time.time() - t0, 1)}
    try:
        rd = results.results_dict or {}
        for k, v in rd.items():
            metrics[k.replace("metrics/", "")] = round(float(v), 4)
    except Exception:
        pass
    best = Path(model.trainer.save_dir) / "weights" / "best.pt"
    version = f"yolo11-{dataset_version}-{time.strftime('%H%M%S')}"
    vdir = Path(MODEL_STORE) / "versions" / version
    vdir.mkdir(parents=True, exist_ok=True)
    ckpt = vdir / "yolo_best.pt"
    if best.exists():
        shutil.copyfile(best, ckpt)
    meta = register_model(version, metrics, DEFAULT_CLASSES, str(ckpt), None, None,
                          architecture="yolo11s", image_size=imgsz, status="testing",
                          activate=False)
    return {"status": "completed", "version": version, "metrics": metrics,
            "stats": stats, "checkpoint_path": str(ckpt), "architecture": "yolo11s",
            "bootstrap_labels": True}
