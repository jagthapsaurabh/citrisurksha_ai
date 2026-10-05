"""Upgrade step 6 (backend): calibration export builder maps reviewed
detections with their stored pipeline evidence; unreviewed rows are excluded."""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.calibration import build_calibration_record, build_calibration_records

AI = {
    "decision": "uncertain", "confidence": 0.6, "model_version": "pipeline-v1|cnn:x|det:opencv_fallback",
    "quality": {"acceptable": True, "failed_checks": []},
    "detector": {"mode": "opencv_fallback", "detections": 1},
    "evidence": {"signals": [{"source": "cnn", "pest_id": "cotton-aphid", "score": 0.52, "weak": True},
                             {"source": "dino_qdrant", "pest_id": "cotton-aphid", "score": 0.8, "weak": False}]},
    "memory": {"top1": {"pest_id": "cotton-aphid"}, "top1_score": 0.8, "top2_score": 0.3,
               "margin": 0.5, "support_count": 3},
    "clip": {"top1": {"pest_id": "citrus-psyllid", "score": 0.4}, "margin": 0.2},
    "candidates": [{"pest_id": "cotton-aphid", "score": 0.8}, {"pest_id": "citrus-thrips", "score": 0.2}],
}


def row(reviewed=True):
    return SimpleNamespace(
        id="det-1", pest_id="cotton-aphid", ai_response=AI,
        reviewed_by="admin-1" if reviewed else None,
        reviewed_at="2026-10-05 10:00:00" if reviewed else None,
        admin_status="corrected" if reviewed else "unreviewed",
        corrected_by_admin=True if reviewed else False,
    )


def test_reviewed_row_exports_with_evidence():
    r = build_calibration_record(row(True))
    assert r is not None
    assert r["label"]["source"] == "expert_review" and r["label"]["pest_id"] == "cotton-aphid"
    f = r["features"]
    assert f["quality_acceptable"] is True
    assert f["memory"]["top1_score"] == 0.8 and f["memory"]["support_count"] == 3
    assert f["clip"]["top1_pest"] == "citrus-psyllid"
    assert f["cnn"]["top1_pest"] == "cotton-aphid"
    assert f["fused"]["top1_pest"] == "cotton-aphid" and f["fused"]["margin"] == 0.6
    assert f["decision"] == "uncertain"


def test_unreviewed_row_never_labelled():
    assert build_calibration_record(row(False)) is None
    assert build_calibration_records([row(False), row(True)])


def test_legacy_detection_without_pipeline_fields():
    r = row(True)
    r.ai_response = {"decision": None, "confidence": 0.5}  # legacy CNN response
    out = build_calibration_record(r)
    assert out is not None
    assert out["features"]["memory"] is None and out["features"]["clip"] is None
    assert out["features"]["fused"]["top1_pest"] is None
