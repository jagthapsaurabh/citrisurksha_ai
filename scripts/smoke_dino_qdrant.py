"""Step 4 smoke validation with REAL pretrained DINOv2 weights + embedded Qdrant.

Indexes the bundled sample images under provisional labels, then checks that
nearest-neighbour retrieval and the pipeline memory signal behave sensibly.
Run manually (not part of the unit suite, which stays weight-free):

  python3 scripts/smoke_dino_qdrant.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

os.environ["MODEL_STORE"] = tempfile.mkdtemp(prefix="cs-smoke-ms-", dir="/home/user/.tmp")
os.environ["QDRANT_PATH"] = tempfile.mkdtemp(prefix="cs-smoke-q-", dir="/home/user/.tmp")
os.environ["DINOV2_ENABLED"] = "true"
os.environ["MEMORY_ENABLED"] = "true"

from PIL import Image  # noqa: E402

from app.embeddings import dino_embedder  # noqa: E402
from app.memory import VisualMemory  # noqa: E402
from app.pipeline import run_pipeline  # noqa: E402

SAMPLES = ROOT / "data" / "sample_images"
LABELS = {
    "leafminer_closeup.jpg": "citrus-leaf-miner",
    "leafminer_mines.png": "citrus-leaf-miner",
    "psyllid_nymphs.jpg": "citrus-psyllid",
    "orchard.jpg": "no-citrus-pest",
}


def main() -> int:
    assert dino_embedder.available, "DINOv2 weights could not be loaded"
    vec = dino_embedder.embed(Image.open(SAMPLES / "leafminer_closeup.jpg").convert("RGB"))
    assert vec is not None and vec.shape == (384,), vec.shape
    print("dino embedding dim:", vec.shape, "norm:", round(float((vec ** 2).sum() ** 0.5), 4))

    mem = VisualMemory()
    records = [{"image_id": name, "image_path": str(SAMPLES / name), "pest_id": pest,
                "stage": "unknown", "source": "smoke", "verification_status": "verified",
                "dataset_version": "smoke-v1"} for name, pest in LABELS.items()]
    print("index:", mem.index_verified(records))
    print("stats:", json.dumps(mem.stats(), indent=1)[:600])

    q = mem.query(vec, top_k=4)
    print("query(leafminer) top1:", q["top1"])
    ok_top1 = q["top1"] and q["top1"]["pest_id"] == "citrus-leaf-miner" and q["top1"]["similarity"] > 0.8

    content = (SAMPLES / "leafminer_closeup.jpg").read_bytes()
    out = run_pipeline(content)
    print("pipeline decision:", out["decision"], "| memory top1:", (out["memory"] or {}).get("top1"))
    ok_mem = out["memory"] is not None and out["memory"]["top1"]["pest_id"] == "citrus-leaf-miner"

    print("SMOKE_OK" if (ok_top1 and ok_mem) else "SMOKE_DEGRADED")
    try:
        mem._client.close()  # silence qdrant-local __del__ at interpreter exit
    except Exception:
        pass
    return 0 if (ok_top1 and ok_mem) else 1


if __name__ == "__main__":
    raise SystemExit(main())
