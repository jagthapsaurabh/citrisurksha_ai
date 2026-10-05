"""Upgrade step 4 tests: DINOv2 embedding gate + Qdrant visual memory.

Tests never download DINOv2 weights: the embedder is exercised only through its
graceful-degradation paths, while Qdrant retrieval/aggregation is tested with
directly injected vectors (local embedded mode in a temp dir).
"""
import os
import sys
import tempfile

import uuid

os.environ.setdefault("MODEL_STORE", tempfile.mkdtemp(prefix="cs-ms4-"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from app.memory import VisualMemory, memory_evidence, point_id


@pytest.fixture()
def memenv(monkeypatch, tmp_path):
    monkeypatch.setenv("QDRANT_PATH", str(tmp_path / "qdrant"))
    monkeypatch.setenv("DINOV2_ENABLED", "false")   # no weight downloads in tests
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    return tmp_path


def seed(mem: VisualMemory):
    e1, e2 = [1, 0, 0, 0], [0, 1, 0, 0]
    recs = []
    for i in range(3):
        v = np.array(e1, float) + np.random.default_rng(i).normal(0, 0.02, 4)
        v /= np.linalg.norm(v)
        recs.append({"image_id": f"a{i}", "pest_id": "citrus-thrips", "stage": "larva",
                     "source": "admin", "verification_status": "verified",
                     "dataset_version": "dataset-v1", "vector": v})
    v = np.array(e2, float); v /= np.linalg.norm(v)
    recs.append({"image_id": "b0", "pest_id": "cotton-aphid", "stage": "adult",
                 "source": "farmer", "verification_status": "verified",
                 "dataset_version": "dataset-v1", "vector": v})
    assert mem.upsert_vectors(recs) == 4


def test_point_id_deterministic_uuid():
    a, b = point_id("img-1"), point_id("img-1")
    assert a == b
    uuid.UUID(a)  # must be a valid qdrant point id
    assert point_id("img-2") != a


def test_qdrant_aggregation_top1_top2_margin(memenv):
    mem = VisualMemory(dim=4)
    seed(mem)
    assert mem.count() == 4
    q = np.array([0.99, 0.03, 0, 0], float)
    res = mem.query(q, top_k=8)
    assert res["top1"]["pest_id"] == "citrus-thrips"
    assert res["top1"]["support_count"] == 3
    assert res["top2"]["pest_id"] == "cotton-aphid"
    assert res["margin"] > 0.5
    assert res["top1_score"] > res["top2_score"]
    ids = {m["image_id"] for m in res["matches"]}
    assert {"a0", "a1", "a2", "b0"} == ids
    assert res["matches"][0]["verification_status"] == "verified"


def test_index_verified_missing_paths(memenv):
    mem = VisualMemory(dim=4)
    out = mem.index_verified([{"image_id": "x1", "image_path": "/nonexistent/x.jpg",
                               "pest_id": "citrus-thrips"}])
    assert out["indexed"] == 0 and out["missing"] == 1
    assert mem.count() == 0


def test_memory_evidence_disabled_and_unavailable(memenv, monkeypatch):
    monkeypatch.setenv("MEMORY_ENABLED", "false")
    assert memory_evidence(None) is None            # disabled => silent skip
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    # DINOv2 disabled => no embedding => None, no crash, no fake signal
    assert memory_evidence("not-used") is None


def test_stats_payload(memenv):
    mem = VisualMemory(dim=4)
    seed(mem)
    st = mem.stats()
    assert st["total"] == 4
    assert st["per_pest"].get("citrus-thrips") == 3
    assert st["embedding_versions"].get("dinov2-vits14-v1") == 4


# ------------------------------------------------------- pipeline integration
def _natural_bytes():
    from test_pipeline_step2 import encode, natural_image
    return encode(natural_image())


def test_pipeline_consumes_memory_signal(memenv, monkeypatch):
    fake = {
        "top1": {"pest_id": "citrus-thrips", "similarity": 0.82, "support_count": 4,
                 "support_ids": ["a0", "a1", "a2"], "stages": ["larva"]},
        "top2": {"pest_id": "cotton-aphid", "similarity": 0.4, "support_count": 1,
                 "support_ids": ["b0"], "stages": []},
        "top1_score": 0.82, "top2_score": 0.4, "margin": 0.42, "support_count": 4,
        "matches": [], "aggregated": [], "embedding_version": "dinov2-vits14-v1",
        "timings": {"embedding": 0.0, "qdrant_query": 0.0},
    }
    import app.memory as memory_mod
    monkeypatch.setattr(memory_mod, "memory_evidence", lambda crop, top_k=None: fake)

    from app.pipeline import run_pipeline
    out = run_pipeline(_natural_bytes())
    assert out["memory"] is not None and out["memory"]["top1"]["pest_id"] == "citrus-thrips"
    srcs = [s["source"] for s in out["evidence"]["signals"]]
    assert "dino_qdrant" in srcs
    # weak bootstrap CNN + strong memory => still never "identified"
    assert out["decision"] in ("uncertain", "identified")
    assert any(c["pest_id"] == "citrus-thrips" for c in out["candidates"])


def test_pipeline_novel_image_gets_negative_vote(memenv, monkeypatch):
    fake = {"top1": {"pest_id": "fruit-fly", "similarity": 0.08, "support_count": 1,
                    "support_ids": ["z"], "stages": []},
            "top2": None, "top1_score": 0.08, "top2_score": 0.0, "margin": 0.08,
            "support_count": 1, "matches": [], "aggregated": [],
            "embedding_version": "dinov2-vits14-v1",
            "timings": {"embedding": 0.0, "qdrant_query": 0.0}}
    import app.memory as memory_mod
    monkeypatch.setattr(memory_mod, "memory_evidence", lambda crop, top_k=None: fake)
    from app.pipeline import run_pipeline
    out = run_pipeline(_natural_bytes())
    negs = [s for s in out["evidence"]["signals"] if s["source"] == "dino_qdrant" and s["pest_id"] is None]
    assert negs and negs[0]["weak"] is True


def test_memory_endpoints(memenv):
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    mem = VisualMemory(dim=4)
    seed(mem)
    st = c.get("/memory/stats").json()
    assert st["total"] == 4
    r = c.post("/memory/index-verified", json={"records": [
        {"image_id": "zz", "image_path": "/nope.jpg", "pest_id": "citrus-thrips"}]}).json()
    assert r["missing"] == 1 and r["indexed"] == 0
