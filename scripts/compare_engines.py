"""Upgrade step 3 harness: run the LEGACY single-CNN engine and the new
multi-stage PIPELINE over the same images and produce a comparison report.

Usage:
  python3 scripts/compare_engines.py [image_dir] [out_json]

No ground truth is assumed: the report shows agreement, honesty (decisions like
poor_image/unknown instead of forced classes) and per-stage latency. Re-run it
after every training round; a pipeline model may replace production only after
this harness plus the frozen-test evaluation (step 13) agree.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))
os.environ.setdefault("MODEL_STORE", str(ROOT / "ai-service" / "model-store"))

from PIL import Image  # noqa: E402

from app.ml import inference_engine  # noqa: E402
from app.pipeline import run_pipeline  # noqa: E402


def main() -> int:
    img_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "sample_images")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "scripts" / "compare_report.json")
    files = sorted([p for p in img_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])[:20]
    if not files:
        print("No images found in", img_dir)
        return 1

    rows = []
    for p in files:
        content = p.read_bytes()
        try:
            img = Image.open(p).convert("RGB")
            t0 = time.perf_counter()
            legacy = inference_engine.predict(img)
            legacy_s = round(time.perf_counter() - t0, 3)
        except Exception as exc:  # pragma: no cover
            legacy, legacy_s = {"pest_name": f"error:{exc}", "confidence": 0, "is_citrus_pest": False}, -1
        t0 = time.perf_counter()
        pipe = run_pipeline(content)
        pipe_s = round(time.perf_counter() - t0, 3)
        rows.append({
            "file": p.name,
            "legacy": {"pest": legacy.get("pest_name"), "conf": legacy.get("confidence"),
                       "is_pest": legacy.get("is_citrus_pest"), "mode": legacy.get("model_version"), "seconds": legacy_s},
            "pipeline": {"decision": pipe.get("decision"), "pest": pipe.get("pest_name"),
                         "conf": pipe.get("confidence"), "is_pest": pipe.get("is_citrus_pest"),
                         "review_priority": pipe.get("review_priority"),
                         "detector_mode": (pipe.get("detector") or {}).get("mode"),
                         "quality_ok": (pipe.get("quality") or {}).get("acceptable"),
                         "timings": pipe.get("timings"), "seconds": pipe_s},
            "pest_agreement": bool(legacy.get("is_citrus_pest")) == bool(pipe.get("is_citrus_pest")),
        })

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "engine_modes": {"legacy": "single-CNN (bootstrap until trained)",
                         "pipeline": "quality->yolo11/fallback->cnn-signal->decision"},
        "images": len(rows),
        "agreement_rate": round(sum(r["pest_agreement"] for r in rows) / len(rows), 3),
        "pipeline_decision_counts": {d: sum(r["pipeline"]["decision"] == d for r in rows)
                                     for d in sorted({r["pipeline"]["decision"] for r in rows})},
        "avg_latency_seconds": {"legacy": round(sum(r["legacy"]["seconds"] for r in rows) / len(rows), 3),
                                "pipeline": round(sum(r["pipeline"]["seconds"] for r in rows) / len(rows), 3)},
        "rows": rows,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"images={len(rows)} agreement={report['agreement_rate']} "
          f"legacy_avg={report['avg_latency_seconds']['legacy']}s pipeline_avg={report['avg_latency_seconds']['pipeline']}s")
    for d, n in report["pipeline_decision_counts"].items():
        print(f"  pipeline decision {d}: {n}")
    print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
