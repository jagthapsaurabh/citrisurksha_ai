"""Operational tool for the real training drive (post-step-12).

Converts a locally collected labelled image folder into governance-ready
training data:

    <src_dir>/<pest_id>/*.jpg|png        (pest_id = one of the 21 class ids,
                                           e.g. citrus-psyllid, no-citrus-pest)

For every image it: validates type/size, dedupes with dHash inside the class,
copies it into storage/training_images/<pest_id>/ and writes a provenance
record (sha256, dhash, source, ingested_at, verified=false).

IMPORTANT: ingested images are UNVERIFIED. They become trainable only after an
expert verifies them in the admin panel (Train AI / Farmer Uploads), exactly as
the release runbook requires. Open dataset sources to collect from are listed
in backend/app/dataset_sources.py and docs/AI_TRAINING.md.

Usage:
  python3 scripts/ingest_labelled_images.py <src_dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

from app.datasets import dhash, hamming  # noqa: E402
from app.model_registry import DEFAULT_CLASSES  # noqa: E402

KNOWN = {c["id"] for c in DEFAULT_CLASSES}
MAGIC = {b"\xff\xd8\xff": "jpeg", b"\x89PNG": "png"}
MIN_BYTES = int(os.getenv("INGEST_MIN_BYTES", "128"))


def sniff(path: Path) -> str | None:
    head = path.read_bytes()[:4]
    for magic, kind in MAGIC.items():
        if head.startswith(magic):
            return kind
    return None


def ingest(src_dir: Path, dest_root: Path, provenance: Path, dry_run: bool = False) -> dict:
    report: dict = {"classes": {}, "copied": 0, "skipped": [], "dry_run": dry_run}
    for cls_dir in sorted([p for p in src_dir.iterdir() if p.is_dir()]):
        pid = cls_dir.name
        if pid not in KNOWN:
            report["skipped"].append({"reason": "unknown-class-folder", "path": str(cls_dir)})
            continue
        seen_hashes: list[int] = []
        per_class = {"copied": 0, "dupes": 0, "invalid": 0}
        for img in sorted(cls_dir.glob("*")):
            if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            kind = sniff(img)
            if kind is None or img.stat().st_size < MIN_BYTES:
                per_class["invalid"] += 1
                continue
            h = dhash(Image.open(img).convert("RGB"))
            if any(hamming(h, s) <= 6 for s in seen_hashes):
                per_class["dupes"] += 1
                continue
            seen_hashes.append(h)
            sha = hashlib.sha256(img.read_bytes()).hexdigest()
            dest = dest_root / pid / f"ingested_{int(time.time())}_{img.name}"
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(img, dest)
                with open(provenance, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "file": str(dest), "pest_id": pid, "source_dir": str(cls_dir),
                        "sha256": sha, "dhash": h, "kind": kind,
                        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "verified": False,
                    }, ensure_ascii=False) + "\n")
            per_class["copied"] += 1
            report["copied"] += 1
        report["classes"][pid] = per_class
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    src = Path(args.src_dir)
    if not src.is_dir():
        print("source dir not found:", src)
        return 1
    dest = ROOT / "storage" / "training_images"
    prov = dest / "provenance.jsonl"
    rep = ingest(src, dest, prov, dry_run=args.dry_run)
    print(json.dumps(rep, indent=2))
    print("\nNext: verify these images in the admin panel, then build a dataset"
          "\nversion and train per docs/RELEASE_RUNBOOK.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
