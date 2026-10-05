"""Upgrade step 6 tests: calibration record schema + threshold/weight proposals."""
import os
import sys
import tempfile

os.makedirs("/home/user/.tmp", exist_ok=True)

os.environ.setdefault("MODEL_STORE", tempfile.mkdtemp(prefix="cs-ms6-", dir="/home/user/.tmp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.calibration import make_record, suggest_thresholds, validate_record


def rec(label, fused_pest, fused_score, dino_score, clip_score=0.3, margin=0.3):
    return make_record(
        image_id="img", label_pest_id=label,
        features={
            "quality_acceptable": True,
            "failed_checks": [],
            "signals": [
                {"source": "dino_qdrant", "pest_id": fused_pest, "score": dino_score, "weak": False},
                {"source": "clip", "pest_id": "citrus-psyllid", "score": clip_score, "weak": True},
            ],
            "fused": {"top1_pest": fused_pest, "top1_score": fused_score, "margin": margin},
            "decision": "identified",
        },
        reviewed_by="admin-1", reviewed_at="2026-10-05")


def test_validate_record_ok_and_errors():
    r = rec("cotton-aphid", "cotton-aphid", 0.8, 0.85)
    ok, errs = validate_record(r)
    assert ok and not errs
    bad = rec("cotton-aphid", "cotton-aphid", 0.8, 0.85)
    bad["record_version"] = 99
    bad["label"]["source"] = "farmer"
    ok, errs = validate_record(bad)
    assert not ok and any("record_version" in e for e in errs) and any("expert_review" in e for e in errs)


def test_suggest_separability_weights():
    records = []
    for _ in range(10):  # correct: dino agrees with label, high fused
        records.append(rec("cotton-aphid", "cotton-aphid", 0.8, 0.85))
    for _ in range(5):   # wrong: dino voted elsewhere (here dino==fused!=label), low fused
        records.append(rec("cotton-aphid", "citrus-thrips", 0.4, 0.4))
    prop = suggest_thresholds(records)
    assert prop["applied"] is False
    w = prop["proposed"]
    assert w["W_DINO"] > w["W_CLIP"]          # dino separates, clip is noise
    assert 0.4 <= w["W_DINO"] <= 0.6
    # identify threshold proposed between wrong and correct fused scores
    assert 0.4 <= prop["proposed"]["DECIDE_IDENTIFY_MIN"] <= 0.8
    assert prop["stats"]["correct"] == 10 and prop["stats"]["wrong"] == 5


def test_suggest_no_data_keeps_defaults():
    prop = suggest_thresholds([])
    assert prop["applied"] is False
    assert prop["proposed"]["DECIDE_IDENTIFY_MIN"] == 0.65
    assert prop["stats"]["records_usable"] == 0


def test_unlabelled_quality_rejected_records_excluded():
    r = rec("cotton-aphid", "cotton-aphid", 0.8, 0.85)
    r["features"]["quality_acceptable"] = False
    prop = suggest_thresholds([r])
    assert prop["stats"]["records_usable"] == 0
