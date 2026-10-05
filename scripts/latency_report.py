"""Step 12: per-stage latency budget report.

  python3 scripts/latency_report.py [--with-heavy]

Runs the pipeline over the bundled sample images, checks every stage against
its budget (ai-service/app/perf.py) and writes scripts/latency_report.json.
Heavy stages (DINOv2/OpenCLIP) are included only with --with-heavy (they need
the weight caches); otherwise they are reported as skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))
os.environ.setdefault("MODEL_STORE", tempfile.mkdtemp(prefix="cs-lat-"))

if "--with-heavy" not in sys.argv:
    os.environ.setdefault("DINOV2_ENABLED", "false")
    os.environ.setdefault("CLIP_ENABLED", "false")

from app.perf import check_budget  # noqa: E402
from app.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-heavy", action="store_true")
    ap.parse_args()
    samples = sorted((ROOT / "data" / "sample_images").glob("*"))
    rows, over = [], []
    if samples:  # warm-up pass: first call pays one-time model loads, not steady state
        run_pipeline(samples[0].read_bytes())
    for p in samples:
        out = run_pipeline(p.read_bytes())
        rep = check_budget(out.get("timings") or {})
        rows.append({"file": p.name, "decision": out["decision"],
                     "timings": out["timings"], "budget": rep})
        if not rep["within_budget"]:
            over.append(p.name)
    report = {"images": len(rows), "over_budget": over, "rows": rows}
    out_path = ROOT / "scripts" / "latency_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for r in rows:
        t = r["timings"]
        print(f"{r['file']}: total {t.get('total')}s decision={r['decision']} "
              f"quality={t.get('opencv_quality')} detector={t.get('detector')} "
              f"cnn={t.get('legacy_cnn')} dino={t.get('dino_qdrant')} clip={t.get('openclip')}")
    print("OVER-BUDGET FILES:", over or "none")
    print("report:", out_path)
    return 0 if not over else 1


if __name__ == "__main__":
    raise SystemExit(main())
