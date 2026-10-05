"""Per-stage latency budgets (upgrade step 12).

Every pipeline stage reports its seconds in `timings`; this module checks them
against configurable budgets so a slow stage can never silently ship. Budgets
are generous CPU defaults - tighten per hardware in env.
"""
from __future__ import annotations

import os

DEFAULT_STAGE_BUDGETS = {
    "opencv_quality": 0.10,
    "detector": 1.50,        # yolo11 on CPU; fallback localiser is ~0.05
    "legacy_cnn": 0.50,
    "dino_qdrant": 1.00,     # embedding + qdrant query
    "openclip": 0.80,
    "decision": 0.05,
}


def stage_budgets() -> dict:
    out = dict(DEFAULT_STAGE_BUDGETS)
    for k in list(out):
        out[k] = float(os.getenv(f"BUDGET_{k.upper()}", str(out[k])))
    return out


def total_budget() -> float:
    return float(os.getenv("LATENCY_TOTAL_BUDGET_S", "3.0"))


def check_budget(timings: dict) -> dict:
    budgets = stage_budgets()
    stages = {}
    for stage, budget in budgets.items():
        measured = timings.get(stage)
        stages[stage] = {
            "measured": measured,
            "budget": budget,
            "ok": (measured is None) or (float(measured) <= budget),
            "skipped": measured is None,
        }
    total = float(timings.get("total") or 0.0)
    t_ok = total <= total_budget()
    return {
        "stages": stages,
        "total": {"measured": total, "budget": total_budget(), "ok": t_ok},
        "within_budget": t_ok and all(s["ok"] for s in stages.values()),
    }
