"""Upgrade step 11 tests: priority-weight tuning from review outcomes and
unknown-image clustering for novel-pest discovery."""
import os
import sys
import tempfile

os.environ["MODEL_STORE"] = tempfile.mkdtemp(prefix="cs-ms11-")
os.environ["QDRANT_PATH"] = tempfile.mkdtemp(prefix="cs-q11-")
os.environ.setdefault("DINOV2_ENABLED", "false")
os.environ.setdefault("CLIP_ENABLED", "false")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from app.active_learning import (extract_signals, store_unknown, tune_priority_weights,
                                 unknown_clusters)


def rec(label, top1, margin):
    return {"label": {"pest_id": label, "source": "expert_review"},
            "features": {"fused": {"top1_pest": top1, "top1_score": 0.5, "margin": margin},
                         "signals": [], "quality_acceptable": True, "decision": "uncertain"}}


def test_tune_lifts_correlated_signal():
    records = [rec("a", "b", 0.02) for _ in range(10)]     # wrong + small margin
    records += [rec("a", "a", 0.3) for _ in range(10)]     # right + big margin
    out = tune_priority_weights(records)
    assert out["applied"] is False
    assert out["proposed"] is not None
    assert out["proposed"]["small_margin"] == max(out["proposed"].values())
    assert out["lifts"]["small_margin"] > 0.4
    assert tune_priority_weights(records[:5])["proposed"] is None   # too little data


def test_extract_signals_flags():
    f = {"fused": {"top1_pest": "x", "top1_score": 0.4, "margin": 0.05},
         "signals": [{"source": "yolo", "pest_id": "x", "score": 0.9, "weak": False},
                     {"source": "cnn", "pest_id": "y", "score": 0.8, "weak": False}],
         "memory": {"support_count": 1, "top1_score": 0.1},
         "clip": {"top1_pest": "z"}}
    s = extract_signals(f)
    assert s["low_conf"] and s["small_margin"] and s["disagreement"]
    assert s["weak_support"] and s["novel_image"] and s["clip_conflict"]


def test_unknown_clustering():
    rng = np.random.default_rng(3)
    e1, e2 = np.array([1, 0, 0, 0.] + [0] * 380), np.array([0, 1, 0, 0.] + [0] * 380)
    for i in range(3):
        v = e1 + rng.normal(0, 0.005, 384); store_unknown(v / np.linalg.norm(v),
                                                        {"image_sha": f"a{i}", "top_candidate": "mystery-a", "decision": "unknown"})
    for i in range(3):
        v = e2 + rng.normal(0, 0.005, 384); store_unknown(v / np.linalg.norm(v),
                                                        {"image_sha": f"b{i}", "top_candidate": "mystery-b", "decision": "unknown"})
    store_unknown(np.array([0, 0, 1, 0.] + [0] * 380), {"image_sha": "out", "decision": "unknown"})

    out = unknown_clusters(similarity=0.9, min_size=3)
    assert out["total_unknowns"] == 7
    sizes = [c["size"] for c in out["clusters"]]
    assert sizes[0] == 3 and sizes[1] == 3 and sizes[-1] == 1
    assert out["clusters"][0]["candidate_new_class"] is True
    assert out["clusters"][-1]["candidate_new_class"] is False
    assert out["clusters"][0]["top_candidate_votes"]


def test_pipeline_stores_unknowns(monkeypatch):
    import app.embeddings as emb
    import app.active_learning as al
    captured = []
    monkeypatch.setattr(al, "store_unknown", lambda v, p: captured.append(p) or True)

    class FakeDino:
        available = True
        def embed_timed(self, img):
            return np.ones(384, dtype=np.float32) / 19.5, 0.001
        def embed(self, img):
            return np.ones(384, dtype=np.float32) / 19.5

    monkeypatch.setattr(emb, "dino_embedder", FakeDino())

    from test_pipeline_step2 import encode, natural_image
    from app.pipeline import run_pipeline
    out = run_pipeline(encode(natural_image()))
    assert out["decision"] in ("unknown", "uncertain")
    assert captured, "unknown crop should be stored for clustering"
    assert captured[0]["decision"] == out["decision"] and captured[0]["image_sha"]
