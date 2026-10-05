"""Dataset versioning with frozen test set + near-duplicate detection (step 7).

Rules honoured:
- The test set is FROZEN at first creation and re-used by later versions;
  training/val splits never contain frozen test ids (no leakage).
- Near-duplicate images (dHash hamming distance <= threshold) inside the same
  class are collapsed (first kept) and reported, so duplicates cannot inflate
  accuracy by appearing in two splits.
- Manifests are immutable JSON files under <model-store>/datasets/<version>.json.
"""
from __future__ import annotations

import json
import os
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

MODEL_STORE = os.getenv("MODEL_STORE", "/app/model-store")


def _datasets_dir() -> Path:
    d = Path(MODEL_STORE) / "datasets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def dhash(img: Image.Image, hash_size: int = 8) -> int:
    """64-bit difference hash; robust, dependency-free perceptual fingerprint."""
    g = img.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    px = list(g.getdata())
    h = 0
    for r in range(hash_size):
        for c in range(hash_size):
            i = r * (hash_size + 1) + c
            if px[i] > px[i + 1]:
                h |= 1 << (r * hash_size + c)
    return h


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _dedupe(records: list[dict], threshold: int) -> tuple[list[dict], int]:
    seen: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    kept: list[dict] = []
    removed = 0
    for rec in records:
        try:
            img = Image.open(rec["image_path"]).convert("RGB")
            h = dhash(img)
        except Exception:
            kept.append(rec)
            continue
        dups = [x for x in seen[rec["pest_id"]] if hamming(x[0], h) <= threshold]
        if dups:
            removed += 1
            continue
        seen[rec["pest_id"]].append((h, rec))
        kept.append(rec)
    return kept, removed


def build_dataset(records: list[dict], version: str,
                  previous_frozen_test_ids: list[str] | None = None,
                  annotation_version: str = "v1",
                  test_fraction: float = 0.2,
                  dup_threshold: int = 6) -> dict:
    """Split verified records into train/val/test with a frozen test set."""
    if not records:
        raise ValueError("No verified records supplied")
    rng = random.Random(42)
    recs, dups_removed = _dedupe(records, dup_threshold)
    by_id = {str(r["image_id"]): r for r in recs}

    frozen = [i for i in (previous_frozen_test_ids or []) if i in by_id]
    if frozen:
        test_ids = frozen
    else:
        test_ids = []
        by_class: dict[str, list[str]] = defaultdict(list)
        for r in recs:
            by_class[r["pest_id"]].append(str(r["image_id"]))
        for cid, ids in by_class.items():
            rng.shuffle(ids)
            k = max(1, int(len(ids) * test_fraction)) if len(ids) >= 2 else 0
            test_ids += ids[:k]

    test_set = set(test_ids)
    rest = [i for i in by_id if i not in test_set]
    train_ids, val_ids = [], []
    by_class_rest: dict[str, list[str]] = defaultdict(list)
    for i in rest:
        by_class_rest[by_id[i]["pest_id"]].append(i)
    for cid, ids in by_class_rest.items():
        rng.shuffle(ids)
        k = max(1, int(len(ids) * 0.2)) if len(ids) >= 3 else 0
        val_ids += ids[:k]
        train_ids += ids[k:]
    if not val_ids and rest:
        val_ids = rest[:1]
        train_ids = [i for i in rest if i not in val_ids]

    split = {i: "test" for i in test_set}
    split.update({i: "val" for i in val_ids})
    split.update({i: "train" for i in train_ids})

    manifest = {
        "version": version,
        "annotation_version": annotation_version,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "image_count": len(recs),
        "class_distribution": dict(Counter(r["pest_id"] for r in recs)),
        "train_count": len(train_ids),
        "val_count": len(val_ids),
        "test_count": len(test_set),
        "frozen_test_ids": sorted(test_set),
        "frozen_inherited": bool(previous_frozen_test_ids),
        "dups_removed": dups_removed,
        "dup_threshold": dup_threshold,
        "splits": split,
    }
    with open(_datasets_dir() / f"{version}.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def load_manifest(version: str) -> dict | None:
    p = _datasets_dir() / f"{version}.json"
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def list_datasets() -> list[dict]:
    out = []
    for p in sorted(_datasets_dir().glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                m = json.load(f)
            out.append({k: m.get(k) for k in
                        ("version", "created_at", "image_count", "train_count",
                         "val_count", "test_count", "dups_removed", "annotation_version")})
        except Exception:
            continue
    return out


def train_val_ids(manifest: dict) -> set[str]:
    return {i for i, s in (manifest.get("splits") or {}).items() if s in ("train", "val")}
