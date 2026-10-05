"""Upgrade step 2 tests: OpenCV quality gate, YOLO11/fallback detector,
crop generation, decision engine, unknown detection, API compatibility."""
import io
import os
import sys
import tempfile


os.environ.setdefault("MODEL_STORE", tempfile.mkdtemp(prefix="cs-modelstore-"))
os.environ.setdefault("DINOV2_ENABLED", "false")  # tests never download weights
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import numpy as np
import pytest

from app.quality import assess_bytes, assess_quality, decode_image
from app.detector import Detector, detector
from app.decision import Signal, ThresholdConfig, decide, fuse, review_priority


# --------------------------------------------------------------------- helpers
def encode(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def natural_image(h=480, w=640, blob=True, seed=7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    img[:] = (40, 130, 60)                                  # green canopy (BGR)
    yy, xx = np.mgrid[0:h, 0:w]
    light = 0.55 + 0.45 * np.sin(xx / 90.0) * np.cos(yy / 70.0)   # daylight gradient
    for c in range(3):
        img[:, :, c] *= light
    img += rng.integers(0, 36, (h, w, 3)).astype(np.float32)      # sensor noise
    img = np.clip(img, 0, 255).astype(np.uint8)
    for i in range(6):                                            # leaf veins
        y0 = int(rng.integers(0, h))
        cv2.line(img, (0, y0), (w, y0 + int(rng.integers(-60, 60))), (25, 80, 35), 2)
    if blob:
        cv2.ellipse(img, (w // 2, h // 2), (70, 48), 20, 0, 360, (60, 120, 150), -1)   # brown insect/damage
        cv2.ellipse(img, (w // 2 + 20, h // 2 - 10), (18, 12), 0, 0, 360, (90, 180, 210), -1)
        cv2.ellipse(img, (w // 2, h // 2), (70, 48), 20, 0, 360, (40, 90, 110), 2)     # sharp edge
    return img


# --------------------------------------------------------------------- quality
def test_quality_rejects_blank():
    blank = np.full((480, 640, 3), 128, np.uint8)
    q = assess_quality(blank)
    assert q["acceptable"] is False
    assert "blur" in q["failed_checks"] and "contrast" in q["failed_checks"]


def test_quality_rejects_dark_and_tiny():
    dark = np.full((300, 300, 3), 8, np.uint8)
    assert assess_quality(dark)["checks"]["brightness"]["ok"] is False
    tiny = natural_image()[:64, :64]
    q = assess_quality(tiny)
    assert q["acceptable"] is False and "resolution" in q["failed_checks"]


def test_quality_accepts_natural_photo():
    q = assess_quality(natural_image())
    assert q["acceptable"] is True, q


def test_quality_corrupt_bytes():
    q = assess_bytes(b"not-an-image-at-all")
    assert q["acceptable"] is False and "corrupt" in q["failed_checks"]


# -------------------------------------------------------------------- detector
def test_fallback_detector_finds_blob_and_crops():
    img = natural_image()
    boxes, meta = detector.detect(img)
    assert meta["mode"] == "opencv_fallback"          # no YOLO weights configured
    assert meta["tiled"] is False                      # normal size => no tiling
    assert len(boxes) >= 1
    b = boxes[0]
    assert 0 <= b["x1"] < b["x2"] <= img.shape[1]
    assert 0 <= b["y1"] < b["y2"] <= img.shape[0]
    crops = Detector.make_crops(img, boxes)
    assert crops and crops[0].shape[0] >= 24 and crops[0].shape[1] >= 24


def test_detector_centre_crop_when_nothing_found():
    img = np.full((300, 300, 3), (40, 130, 60), np.uint8)  # pure green, no blob
    crops = Detector.make_crops(img, [])
    assert len(crops) == 1 and crops[0].shape[:2] == (204, 204)


def test_tiling_only_for_high_resolution():
    big = natural_image(h=2000, w=2400)
    _, meta = detector.detect(big)
    assert meta["tiled"] is True
    small = natural_image()
    _, meta2 = detector.detect(small)
    assert meta2["tiled"] is False


# -------------------------------------------------------------------- decision
def cfg():
    return ThresholdConfig.load()


def test_decision_poor_image():
    q = {"acceptable": False, "failed_checks": ["resolution"], "advice": "Too small."}
    d = decide(q, [], [], [], cfg())
    assert d["decision"] == "poor_image"


def test_decision_non_target_scene():
    q = {"acceptable": False, "failed_checks": ["scene", "blur"], "checks": {"scene": {"ok": False}}, "advice": "x"}
    d = decide(q, [], [], [], cfg())
    assert d["decision"] == "non_target_image"


def test_decision_no_pest_when_all_negative():
    q = {"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}}
    sigs = [Signal("cnn", None, 0.9)]
    cand, neg = fuse(sigs, cfg())
    d = decide(q, cand, neg, sigs, cfg())
    assert d["decision"] == "no_pest_detected"


def test_models_disagreement_becomes_uncertain_not_aphid():
    """The spec's canonical example: YOLO aphid .9, DINO/Qdrant thrips, CLIP psyllid
    must be UNCERTAIN, never blindly Aphid."""
    q = {"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}}
    sigs = [
        Signal("yolo", "cotton-aphid", 0.90),
        Signal("dino_qdrant", "citrus-thrips", 0.80),
        Signal("clip", "citrus-psyllid", 0.70),
    ]
    cand, neg = fuse(sigs, cfg())
    d = decide(q, cand, neg, sigs, cfg(), support_count=5)
    assert d["decision"] == "uncertain"


def test_agreement_high_confidence_identified():
    q = {"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}}
    sigs = [Signal("yolo", "cotton-aphid", 0.9), Signal("cnn", "cotton-aphid", 0.85),
            Signal("dino_qdrant", "cotton-aphid", 0.8)]
    cand, neg = fuse(sigs, cfg())
    d = decide(q, cand, neg, sigs, cfg(), support_count=4)
    assert d["decision"] == "identified" and d["pest_id"] == "cotton-aphid"
    assert d["confidence"] >= 0.65


def test_weak_only_evidence_never_identified():
    """Bootstrap/untrained signals may guide, never confirm."""
    q = {"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}}
    sigs = [Signal("cnn", "citrus-psyllid", 0.52, weak=True)]
    cand, neg = fuse(sigs, cfg())
    d = decide(q, cand, neg, sigs, cfg())
    assert d["decision"] in ("uncertain", "unknown")


def test_small_margin_uncertain_and_priority():
    q = {"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}}
    sigs = [Signal("yolo", "citrus-psyllid", 0.6), Signal("yolo", "cotton-aphid", 0.58)]
    cand, neg = fuse(sigs, cfg())
    d = decide(q, cand, neg, sigs, cfg(), support_count=3)
    assert d["decision"] == "uncertain"
    assert review_priority(d) >= review_priority({"decision": "identified", "confidence": 0.95})


# ------------------------------------------------------------------ API compat
def _client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def _post(img_bytes):
    return _client().post("/predict", files={"image": ("i.jpg", img_bytes, "image/jpeg")})


def test_api_pipeline_mode_additive_contract(monkeypatch):
    monkeypatch.setenv("AI_ENGINE", "pipeline")
    r = _post(encode(natural_image()))
    assert r.status_code == 200
    j = r.json()
    # legacy contract intact
    assert set(["is_citrus_pest", "pest_name", "confidence", "severity_level",
                "model_version", "top_k", "explanation"]) <= set(j)
    # additive pipeline fields
    assert j["decision"] in ["identified", "uncertain", "unknown", "poor_image",
                             "no_pest_detected", "non_target_image"]
    assert "quality" in j and "detector" in j and "timings" in j and "review_priority" in j


def test_api_pipeline_poor_image_honest(monkeypatch):
    monkeypatch.setenv("AI_ENGINE", "pipeline")
    blank = np.full((480, 640, 3), 128, np.uint8)
    j = _post(encode(blank)).json()
    assert j["decision"] in ("poor_image", "non_target_image")
    assert j["is_citrus_pest"] is False


def test_api_legacy_mode_unchanged(monkeypatch):
    monkeypatch.setenv("AI_ENGINE", "legacy")
    j = _post(encode(natural_image())).json()
    assert j["decision"] is None          # legacy engine adds no pipeline fields
    assert "model_version" in j


def test_pipeline_info_endpoint(monkeypatch):
    monkeypatch.setenv("AI_ENGINE", "pipeline")
    j = _client().get("/pipeline/info").json()
    assert j["engine"] == "pipeline" and j["paid_ai_services"] is False
    assert "yolo11_detector" in j["stages"]
