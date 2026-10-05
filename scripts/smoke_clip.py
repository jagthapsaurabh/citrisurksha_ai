"""Step 5 smoke validation with REAL OpenCLIP weights (ViT-B-32, openai).

Reports zero-shot top-3 over the 21 classes for the bundled sample images.
Informational only - CLIP is a secondary weak signal by design; no accuracy
claims are made from this script.

  python3 scripts/smoke_clip.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))
os.environ["MODEL_STORE"] = tempfile.mkdtemp(prefix="cs-smoke-clip-")
os.environ["CLIP_ENABLED"] = "true"

from PIL import Image  # noqa: E402

from app.clip_signal import clip_scorer  # noqa: E402
from app.model_registry import DEFAULT_CLASSES  # noqa: E402

SAMPLES = ROOT / "data" / "sample_images"
NAMES = {c["id"]: c["name"] for c in DEFAULT_CLASSES}


def main() -> int:
    assert clip_scorer.available, "OpenCLIP weights could not be loaded"
    ok = True
    for fname in ["leafminer_closeup.jpg", "psyllid_nymphs.jpg", "orchard.jpg"]:
        res = clip_scorer.score(Image.open(SAMPLES / fname).convert("RGB"))
        order = sorted(res["scores"].items(), key=lambda kv: kv[1], reverse=True)[:3]
        print(f"{fname}: " + ", ".join(f"{NAMES.get(k, k)}={v}" for k, v in order)
              + f"  ({res['seconds']}s)")
        ok = ok and len(res["scores"]) == 21
    print("SMOKE_CLIP_OK" if ok else "SMOKE_CLIP_DEGRADED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
