"""First experimental drive training (open-licensed MIT transfer classes).

Builds dataset-drive-v1 from ingested open-drive images, trains an experimental
CNN classifier and a bootstrap YOLO detector, and writes an honest report.
NOT a production model: production requires expert-verified citrus images
(docs/RELEASE_RUNBOOK.md).

  python3 scripts/run_drive_training.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MODEL_STORE", str(ROOT / "ai-service" / "model-store"))
os.environ["STRICT_20_CLASS_TRAINING"] = "false"   # experimental transfer run only
sys.path.insert(0, str(ROOT / "ai-service"))

from app.datasets import build_dataset, load_manifest  # noqa: E402
from app.ml import train_classifier  # noqa: E402
from app.yolo_train import train_yolo  # noqa: E402

CLASSES = ["citrus-leaf-miner", "no-citrus-pest", "citrus-thrips", "yellow-citrus-thrips", "oriental-spider-mite", "cotton-aphid"]


def collect_records() -> list[dict]:
    recs = []
    for cid in CLASSES:
        d = ROOT / "storage" / "training_images" / cid
        for f in sorted(d.glob("*")):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png") and "ingested" in f.name:
                recs.append({"image_id": f.stem, "image_path": str(f), "pest_id": cid})
    return recs


def main() -> int:
    recs = collect_records()
    print("records:", len(recs))
    manifest = build_dataset(recs, "dataset-drive-v2")
    print("manifest:", {k: manifest[k] for k in ("image_count", "train_count", "val_count", "test_count", "dups_removed")})

    m = load_manifest("dataset-drive-v2")
    train_val = [r for r in recs if m["splits"].get(r["image_id"]) in ("train", "val")]

    t0 = time.time()
    cnn = train_classifier({
        "dataset_version": "dataset-drive-v2", "base_model": "resnet18",
        "epochs": 8, "batch_size": 8, "image_size": 128,
        "classes": [{"id": c, "name": c.replace("-", " ").title()} for c in CLASSES],
        "training_records": train_val,
    })
    cnn_sec = round(time.time() - t0, 1)

    report_partial = {"cnn": {"status": cnn.get("status"), "version": cnn.get("version"), "accuracy": (cnn.get("metrics") or {}).get("accuracy"), "macro_f1": (cnn.get("metrics") or {}).get("macro_f1")}, "yolo": None}
    (ROOT / "docs" / "pilot" / "drive_run_report.md").write_text("# Drive training (partial)\n```json\n" + json.dumps(report_partial, indent=2) + "\n```\n", encoding="utf-8")
    t0 = time.time()
    try:
        yolo = train_yolo({"dataset_version": "dataset-drive-v2", "records": recs,
                       "splits": m["splits"], "epochs": 2, "imgsz": 192, "batch": 1})
    except Exception as exc:
        yolo = {"status": "failed", "error": str(exc)}
    yolo_sec = round(time.time() - t0, 1)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "purpose": "Experimental transfer-learning run on open-licensed (MIT) proxy classes. NOT production.",
        "dataset": {"version": "dataset-drive-v2", **{k: manifest[k] for k in
                   ("image_count", "train_count", "val_count", "test_count", "dups_removed")},
                    "classes": CLASSES},
        "cnn": {"status": cnn.get("status"), "version": cnn.get("version"),
                "accuracy": (cnn.get("metrics") or {}).get("accuracy"),
                "macro_f1": (cnn.get("metrics") or {}).get("macro_f1"),
                "per_class": (cnn.get("metrics") or {}).get("per_class"),
                "seconds": cnn_sec},
        "yolo": {"status": yolo.get("status"), "version": yolo.get("version"),
                 "metrics": yolo.get("metrics"), "bootstrap_labels": True, "seconds": yolo_sec},
        "honesty": "Proxy classes (generic thrips/aphids + Scirtothrips dorsalis) are transfer data only. "
                   "Production models require expert-verified images of the 20 citrus pests.",
    }
    out = ROOT / "docs" / "pilot" / "drive_run_report.md"
    out.write_text("# First experimental drive training\n\n```json\n" +
                   json.dumps(report, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(report, indent=2)[:2200])
    print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
