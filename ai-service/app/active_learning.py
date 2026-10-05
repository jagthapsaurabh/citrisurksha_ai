"""Active learning loop closure (upgrade step 11).

1. Priority-weight tuning from review outcomes: calibration records carry the
   pipeline evidence (features) plus the expert label, so we know WHEN the AI
   was wrong. Signals that correlate with wrongness should raise review
   priority. Proposals only - never auto-applied.

2. Unknown-image clustering: crops the pipeline could not identify are stored
   as DINOv2 embeddings in a dedicated Qdrant collection. Greedy leader
   clustering surfaces visually coherent groups of "unknowns" - candidates for
   NEW pest classes before anyone has named them.
"""
from __future__ import annotations

import os
import time
import uuid

import numpy as np

from .embeddings import EMBEDDING_VERSION
from .memory import COLLECTION, _client

UNKNOWN_COLLECTION = os.getenv("UNKNOWN_COLLECTION", "unknown_pest_candidates")

PRIORITY_SIGNALS = ["low_conf", "small_margin", "disagreement", "weak_support",
                    "novel_image", "clip_conflict"]


# -------------------------------------------------------------------------- 1
def extract_signals(features: dict) -> dict:
    fused = features.get("fused") or {}
    mem = features.get("memory") or {}
    clip = features.get("clip") or {}
    sigs = [s for s in features.get("signals") or [] if s.get("pest_id")]
    strong = {s["pest_id"] for s in sigs if not s.get("weak") and s.get("score", 0) >= 0.5}
    return {
        "low_conf": (fused.get("top1_score") or 0) < 0.55,
        "small_margin": (fused.get("margin") or 0) < 0.08,
        "disagreement": len(strong) > 1,
        "weak_support": mem is not None and (mem.get("support_count") or 0) < 2,
        "novel_image": mem is not None and (mem.get("top1_score") or 0) < 0.25,
        "clip_conflict": bool(clip) and clip.get("top1_pest") not in (None, fused.get("top1_pest")),
    }


def was_wrong(rec: dict) -> bool:
    label = (rec.get("label") or {}).get("pest_id")
    fused = (rec.get("features") or {}).get("fused") or {}
    if label is None:
        return (rec.get("features") or {}).get("decision") not in ("no_pest_detected", "non_target_image")
    return fused.get("top1_pest") != label


def tune_priority_weights(records: list[dict]) -> dict:
    """Lift-based proposal: weight(signal) = P(wrong | signal) - P(wrong)."""
    usable = [r for r in records if isinstance(r, dict) and r.get("features")]
    if len(usable) < 10:
        return {"applied": False, "proposed": None,
                "note": "Need >=10 labelled review outcomes to tune.", "stats": {}}
    wrong = [was_wrong(r) for r in usable]
    p_wrong = sum(wrong) / len(usable)
    stats, lifts = {}, {}
    for sig in PRIORITY_SIGNALS:
        hit = [w for r, w in zip(usable, wrong) if extract_signals(r["features"]).get(sig)]
        p_given = sum(hit) / len(hit) if hit else 0.0
        lifts[sig] = round(p_given - p_wrong, 4)
        stats[sig] = {"count": len(hit), "p_wrong_given_signal": round(p_given, 4)}
    positive = {k: max(0.0, v) for k, v in lifts.items()}
    total = sum(positive.values())
    proposed = {k: round(0.5 + (v / total if total else 0.0), 3) for k, v in positive.items()}
    return {"applied": False, "proposed": proposed, "base_wrong_rate": round(p_wrong, 4),
            "lifts": lifts, "stats": stats,
            "note": "Proposal only. Set ACTIVE_LEARNING_WEIGHTS json after review."}


# -------------------------------------------------------------------------- 2
def _ensure_unknown_collection(client) -> None:
    from qdrant_client import models as qm
    names = [c.name for c in client.get_collections().collections]
    if UNKNOWN_COLLECTION not in names:
        client.create_collection(UNKNOWN_COLLECTION,
                                 vectors_config=qm.VectorParams(size=384, distance=qm.Distance.COSINE))


def store_unknown(vector: np.ndarray, payload: dict) -> bool:
    """Remember an unidentified crop for later clustering."""
    try:
        from qdrant_client import models as qm
        client = _client()
        _ensure_unknown_collection(client)
        client.upsert(UNKNOWN_COLLECTION, [qm.PointStruct(
            id=str(uuid.uuid4()), vector=[float(v) for v in vector],
            payload={**payload, "embedding_version": EMBEDDING_VERSION,
                     "stored_at": time.strftime("%Y-%m-%dT%H:%M:%S")})])
        return True
    except Exception:
        return False


def unknown_clusters(similarity: float | None = None, min_size: int | None = None) -> dict:
    """Greedy leader clustering over stored unknowns (cosine >= similarity)."""
    similarity = float(os.getenv("CLUSTER_SIM", "0.80")) if similarity is None else similarity
    min_size = int(os.getenv("CLUSTER_MIN", "3")) if min_size is None else min_size
    try:
        client = _client()
        names = [c.name for c in client.get_collections().collections]
        if UNKNOWN_COLLECTION not in names:
            return {"clusters": [], "total_unknowns": 0}
        points, nxt = [], None
        while True:
            batch, nxt = client.scroll(UNKNOWN_COLLECTION, limit=500,
                                       with_payload=True, with_vectors=True, offset=nxt)
            points += batch
            if not nxt:
                break
    except Exception:
        return {"clusters": [], "total_unknowns": 0}

    leaders: list[dict] = []
    for p in points:
        v = np.asarray(p.vector, dtype=float)
        v = v / (np.linalg.norm(v) or 1)
        placed = False
        for c in leaders:
            if float(np.dot(v, c["vec"])) >= similarity:
                c["members"].append(p.payload or {})
                c["n"] += 1
                placed = True
                break
        if not placed:
            leaders.append({"vec": v, "members": [p.payload or {}], "n": 1})

    clusters = []
    for c in sorted(leaders, key=lambda x: x["n"], reverse=True):
        votes: dict = {}
        for m in c["members"]:
            t = m.get("top_candidate")
            if t:
                votes[t] = votes.get(t, 0) + 1
        clusters.append({
            "size": c["n"],
            "candidate_new_class": c["n"] >= min_size,
            "top_candidate_votes": votes,
            "sample_image_shas": [m.get("image_sha") for m in c["members"][:5]],
        })
    return {"clusters": clusters, "total_unknowns": len(points),
            "similarity": similarity, "min_size": min_size}
