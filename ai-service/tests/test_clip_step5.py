"""Upgrade step 5 tests: OpenCLIP prompt configuration, degradation and the
rule that CLIP is secondary evidence only (weight-free - no model download)."""
import json
import os
import sys
import tempfile


os.environ.setdefault("MODEL_STORE", tempfile.mkdtemp(prefix="cs-ms5-"))
os.environ.setdefault("DINOV2_ENABLED", "false")
os.environ.setdefault("CLIP_ENABLED", "false")  # unit tests never download weights
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.clip_signal import ClipScorer, clip_evidence, DEFAULT_TEMPLATES
from app.model_registry import DEFAULT_CLASSES


def test_default_prompts_cover_all_classes():
    ids, prompts, counts = ClipScorer.prompts_for(DEFAULT_CLASSES)
    assert len(ids) == len(DEFAULT_CLASSES) == len(counts)
    assert sum(counts) == len(prompts)
    # bundled override file is picked up by default for psyllid
    assert any("psyllid" in p for p in prompts)
    neg = ids.index("no-citrus-pest")
    assert counts[neg] == 2


def test_prompt_override_file(monkeypatch, tmp_path):
    p = tmp_path / "prompts.json"
    p.write_text(json.dumps({"citrus-thrips": ["a photo of tiny thrips on citrus fruit"]}))
    monkeypatch.setenv("CLIP_PROMPTS_FILE", str(p))
    ids, prompts, counts = ClipScorer.prompts_for(DEFAULT_CLASSES)
    i = ids.index("citrus-thrips")
    assert counts[i] == 1 and "tiny thrips" in prompts[sum(counts[:i])]


def test_clip_disabled_returns_none(monkeypatch):
    monkeypatch.setenv("CLIP_ENABLED", "false")
    assert clip_evidence("unused") is None
    monkeypatch.setenv("CLIP_ENABLED", "true")
    monkeypatch.setenv("CLIP_MODEL", "not-a-model")  # load must fail gracefully
    import app.clip_signal as cs
    scorer = cs.ClipScorer()
    assert scorer.score("unused") is None


# ------------------------------------------------------------- pipeline rules
def _natural_bytes():
    from test_pipeline_step2 import encode, natural_image
    return encode(natural_image())


def test_clip_alone_can_never_identify(monkeypatch):
    """A 0.95 zero-shot CLIP vote with no other evidence must NOT produce
    'identified' - CLIP is secondary by design."""
    import app.clip_signal as cs
    monkeypatch.setenv("CLIP_ENABLED", "true")
    monkeypatch.setattr(cs, "clip_evidence", lambda crop, classes=None: {
        "model": "ViT-B-32", "scores": {}, "top1": {"pest_id": "citrus-psyllid", "score": 0.95},
        "top2": {"pest_id": "cotton-aphid", "score": 0.02}, "margin": 0.93, "seconds": 0.0})
    # also silence the memory stage so CLIP is the only positive source
    import app.memory as mm
    monkeypatch.setattr(mm, "memory_evidence", lambda crop, top_k=None: None)
    from app.pipeline import run_pipeline
    out = run_pipeline(_natural_bytes())
    assert out["clip"]["top1"]["pest_id"] == "citrus-psyllid"
    sigs = out["evidence"]["signals"]
    clip_sig = [s for s in sigs if s["source"] == "clip"]
    assert clip_sig and clip_sig[0]["weak"] is True
    assert out["decision"] != "identified"


def test_clip_contradiction_forces_uncertain(monkeypatch):
    """Strong YOLO + strong DINO vs a strong disagreeing CLIP => uncertain."""
    import app.clip_signal as cs
    import app.memory as mm
    monkeypatch.setenv("CLIP_ENABLED", "true")
    monkeypatch.setattr(cs, "clip_evidence", lambda crop, classes=None: {
        "model": "ViT-B-32", "scores": {}, "top1": {"pest_id": "citrus-psyllid", "score": 0.9},
        "top2": {"pest_id": "cotton-aphid", "score": 0.05}, "margin": 0.85, "seconds": 0.0})
    monkeypatch.setattr(mm, "memory_evidence", lambda crop, top_k=None: {
        "top1": {"pest_id": "cotton-aphid", "similarity": 0.88, "support_count": 5,
                 "support_ids": ["a", "b"], "stages": []},
        "top2": None, "top1_score": 0.88, "top2_score": 0.0, "margin": 0.88,
        "support_count": 5, "matches": [], "aggregated": [],
        "embedding_version": "dinov2-vits14-v1", "timings": {}})
    from app.decision import Signal, ThresholdConfig, decide, fuse
    sigs = [Signal("yolo", "cotton-aphid", 0.9),
            Signal("dino_qdrant", "cotton-aphid", 0.88),
            Signal("clip", "citrus-psyllid", 0.9, weak=True)]
    cand, neg = fuse(sigs, ThresholdConfig.load())
    d = decide({"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}},
               cand, neg, sigs, ThresholdConfig.load(), support_count=5)
    # weak CLIP does not overturn two strong agreeing sources...
    assert d["pest_id"] == "cotton-aphid"
    # ...but if CLIP were strong (not weak), disagreement must win:
    sigs2 = [Signal("yolo", "cotton-aphid", 0.9), Signal("clip", "citrus-psyllid", 0.9, weak=False)]
    cand2, neg2 = fuse(sigs2, ThresholdConfig.load())
    d2 = decide({"acceptable": True, "failed_checks": [], "checks": {"scene": {"ok": True}}},
                cand2, neg2, sigs2, ThresholdConfig.load(), support_count=5)
    assert d2["decision"] == "uncertain"


def test_pipeline_info_lists_clip(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("AI_ENGINE", "pipeline")
    j = TestClient(app).get("/pipeline/info").json()
    assert "openclip_signal" in j["stages"]
    assert j["clip"]["role"] == "secondary weak signal only"
