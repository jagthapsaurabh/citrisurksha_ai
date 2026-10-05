"""Step 9 CLI: build a bootstrap YOLO dataset from a folder of verified,
per-class image directories (or from a dataset manifest via the AI service).

Layout expected for folder mode:
  <images_dir>/<pest_id>/*.jpg

Usage:
  python3 scripts/bootstrap_yolo_annotations.py <images_dir> <out_dir> [--manifest dataset-v1]

Full-image boxes are BOOTSTRAP quality; experts should replace them with tight
boxes over time. The frozen test split (manifest mode) stays separate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

from app.yolo_train import build_yolo_dataset  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--manifest", default=None, help="dataset version known to the AI service")
    ap.add_argument("--ai-url", default="http://localhost:8100")
    args = ap.parse_args()

    splits, records = None, []
    img_dir = Path(args.images_dir)
    if args.manifest:
        import requests
        m = requests.get(f"{args.ai_url}/datasets/{args.manifest}", timeout=30).json()
        splits = m.get("splits")
    for cls_dir in sorted([p for p in img_dir.iterdir() if p.is_dir()]):
        for f in sorted(cls_dir.glob("*")):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                records.append({"image_id": f.stem, "image_path": str(f), "pest_id": cls_dir.name})

    stats = build_yolo_dataset(records, args.out_dir, splits=splits)
    print(json.dumps(stats, indent=2))
    return 0 if stats["written"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
