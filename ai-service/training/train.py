"""
Standalone production training entrypoint for CitriSurksha.

This script uses the same real PyTorch/TorchVision training implementation used by
`POST /train/jobs` in the AI service (`app.ml.train_classifier`). It is useful for
running longer training jobs from CLI/cron/systemd/GPU workers.

Example:
  python ai-service/training/train.py \
    --manifest ai-service/training/dataset_manifest_example.json \
    --output-dir ai-service/model-store/cli-runs/run-001 \
    --base-model mobilenet_v3_small \
    --epochs 10 \
    --batch-size 8

Manifest format:
{
  "dataset_version": "2026-07-production-v1",
  "classes": [{"id":"citrus-psyllid", "name":"Asian citrus psyllid"}],
  "training_records": [
    {"image_path":"/absolute/or/relative/path.jpg", "pest_id":"citrus-psyllid", "stage":"adult"}
  ],
  "knowledge_records": []
}

No paid AI service is used. TorchVision models are created with weights=None and
trained from CitriSurksha verified data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow importing ai-service/app when this script is run from project root or ai-service.
THIS_FILE = Path(__file__).resolve()
AI_SERVICE_ROOT = THIS_FILE.parents[1]
PROJECT_ROOT = AI_SERVICE_ROOT.parent
sys.path.insert(0, str(AI_SERVICE_ROOT))

from app.ml import train_classifier  # noqa: E402


def normalize_manifest(manifest: dict, manifest_dir: Path, base_model: str, epochs: int, batch_size: int) -> dict:
    records = []
    for row in manifest.get("training_records") or []:
        row = dict(row)
        path = row.get("image_path") or row.get("path")
        if path and not Path(path).is_absolute():
            candidate = (manifest_dir / path).resolve()
            row["image_path"] = str(candidate)
        records.append(row)

    # Backward-compatible support for old split format.
    if not records and manifest.get("splits"):
        for split_name, split_rows in manifest["splits"].items():
            for row in split_rows:
                image_uri = row.get("image_uri") or row.get("image_path") or row.get("path")
                if image_uri and image_uri.startswith("file://"):
                    image_uri = image_uri.replace("file://", "", 1)
                if image_uri and not image_uri.startswith("s3://"):
                    p = Path(image_uri)
                    if not p.is_absolute():
                        p = (manifest_dir / p).resolve()
                    records.append({
                        "image_path": str(p),
                        "pest_id": row.get("label") or row.get("pest_id"),
                        "stage": row.get("stage"),
                        "source": f"manifest:{split_name}",
                    })

    classes = manifest.get("classes") or []
    classes = [{"id": c, "name": c.replace("-", " ").title()} if isinstance(c, str) else c for c in classes]

    return {
        "dataset_version": manifest.get("dataset_version") or "cli-training",
        "base_model": base_model or manifest.get("base_model") or "mobilenet_v3_small",
        "epochs": epochs or int(manifest.get("epochs", 3)),
        "batch_size": batch_size or int(manifest.get("batch_size", 8)),
        "classes": classes,
        "training_records": records,
        "knowledge_records": manifest.get("knowledge_records") or [],
        "image_size": int(manifest.get("image_size", 224)),
        "learning_rate": float(manifest.get("learning_rate", 1e-3)),
    }


def train(manifest_path: str, output_dir: str, base_model: str, epochs: int, batch_size: int):
    manifest_file = Path(manifest_path).resolve()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    payload = normalize_manifest(manifest, manifest_file.parent, base_model, epochs, batch_size)

    if output_dir:
        os.environ.setdefault("MODEL_STORE", str(Path(output_dir).resolve()))

    result = train_classifier(payload)
    out = Path(output_dir) if output_dir else Path(os.environ.get("MODEL_STORE", "model-store"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "cli_training_result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", default="ai-service/model-store/cli-run")
    parser.add_argument("--base-model", default="mobilenet_v3_small", choices=["mobilenet_v3_small", "mobilenet_v3_large", "resnet18", "efficientnet_b0"])
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    train(args.manifest, args.output_dir, args.base_model, args.epochs, args.batch_size)
