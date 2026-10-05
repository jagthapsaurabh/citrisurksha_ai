"""Step 6 calibration CLI.

Usage:
  1. Export labelled records from the admin panel:
       curl -H "Authorization: Bearer $TOKEN" \
            "http://localhost:8000/admin/ai/calibration-export?limit=1000" > export.json
  2. Propose thresholds/weights:
       python3 scripts/calibrate_decision.py export.json --out proposal.json

The proposal is NEVER applied automatically - review the stats and copy the
values you accept into .env (DECIDE_* / W_* variables), then re-run the
compare harness and frozen-test evaluation before deploying.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

from app.calibration import suggest_thresholds, write_proposal  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("export_json")
    ap.add_argument("--out", default=str(ROOT / "scripts" / "decision_config_proposal.json"))
    args = ap.parse_args()

    data = json.loads(Path(args.export_json).read_text())
    records = data.get("records") if isinstance(data, dict) else data
    proposal = suggest_thresholds(records or [])
    write_proposal(proposal, args.out)
    print(json.dumps(proposal, indent=2))
    print("proposal written to", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
