"""Upgrade step 12 tests: latency budget checker."""
import os
import sys
import tempfile

os.environ["MODEL_STORE"] = tempfile.mkdtemp(prefix="cs-ms12-")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.perf import check_budget


def test_within_budget():
    timings = {"opencv_quality": 0.02, "detector": 0.05, "legacy_cnn": 0.3,
               "dino_qdrant": 0.4, "openclip": 0.2, "decision": 0.001, "total": 1.0}
    rep = check_budget(timings)
    assert rep["within_budget"] is True
    assert rep["stages"]["detector"]["ok"] is True


def test_over_budget_stage_flags():
    timings = {"opencv_quality": 0.02, "detector": 4.0, "legacy_cnn": 0.3,
               "decision": 0.001, "total": 4.4}
    rep = check_budget(timings)
    assert rep["within_budget"] is False
    assert rep["stages"]["detector"]["ok"] is False
    assert rep["stages"]["openclip"]["skipped"] is True   # skipped stages never fail


def test_total_budget_env(monkeypatch):
    monkeypatch.setenv("LATENCY_TOTAL_BUDGET_S", "0.5")
    rep = check_budget({"total": 0.8})
    assert rep["total"]["ok"] is False and rep["within_budget"] is False
