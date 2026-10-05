"""Qdrant visual memory (upgrade step 4).

Qdrant is the VECTOR memory of verified pest images - it is NOT the pest
knowledge database (PostgreSQL keeps symptoms/cure/translations/advisories).

Stored payload per point: image_id, pest_id, pest_class, stage,
dataset_version, verification_status, source, embedding_version.

For a new crop: DINOv2 embedding -> Qdrant top-k -> aggregate evidence by pest
-> top matches, similarity, support ids, top-1/top-2 score and margin.
"""
from __future__ import annotations

import os
import time
import uuid

import numpy as np
from PIL import Image

from .embeddings import EMBEDDING_DIM, EMBEDDING_VERSION, dino_embedder

COLLECTION = os.getenv("MEMORY_COLLECTION", "pest_visual_memory")
NAMESPACE = uuid.UUID("8b6d0d4c-5f3e-4b1a-9c27-000000000000")


_CLIENT_CACHE: dict = {}


def _client():
    """Cached Qdrant client (one per backend target). Local embedded mode keeps
    a single in-process state; per-request clients would fork the storage."""
    from qdrant_client import QdrantClient
    url = os.getenv("QDRANT_URL", "").strip()
    if url:
        key = url
        if key not in _CLIENT_CACHE:
            kwargs = {"url": url}
            api_key = os.getenv("QDRANT_API_KEY", "").strip()
            if api_key:
                kwargs["api_key"] = api_key
            _CLIENT_CACHE[key] = QdrantClient(**kwargs)
        return _CLIENT_CACHE[key]
    path = os.getenv("QDRANT_PATH", "").strip()
    if not path:
        path = os.path.join(os.getenv("MODEL_STORE", "/app/model-store"), "qdrant")
    key = os.path.abspath(path)
    if key not in _CLIENT_CACHE:
        os.makedirs(path, exist_ok=True)
        _CLIENT_CACHE[key] = QdrantClient(path=path)
    return _CLIENT_CACHE[key]


def point_id(image_id: str) -> str:
    return str(uuid.uuid5(NAMESPACE, str(image_id)))


class VisualMemory:
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self._client = None

    def client(self):
        if self._client is None:
            self._client = _client()
            self._ensure_collection()
        return self._client

    def _ensure_collection(self):
        from qdrant_client import models as qm
        c = self._client
        try:
            cols = [x.name for x in c.get_collections().collections]
        except Exception:
            cols = []
        if COLLECTION not in cols:
            c.create_collection(COLLECTION, vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE))

    # ------------------------------------------------------------ write path
    def upsert_vectors(self, records: list[dict]) -> int:
        """records: [{image_id, pest_id, stage, dataset_version, source,
        verification_status, vector}]"""
        from qdrant_client import models as qm
        points = []
        for r in records:
            points.append(qm.PointStruct(
                id=point_id(r["image_id"]),
                vector=[float(v) for v in r["vector"]],
                payload={
                    "image_id": str(r["image_id"]),
                    "pest_id": r.get("pest_id"),
                    "pest_class": r.get("pest_id"),
                    "stage": r.get("stage"),
                    "dataset_version": r.get("dataset_version"),
                    "verification_status": r.get("verification_status", "verified"),
                    "source": r.get("source"),
                    "embedding_version": r.get("embedding_version", EMBEDDING_VERSION),
                },
            ))
        if points:
            self.client().upsert(COLLECTION, points)
        return len(points)

    def index_verified(self, records: list[dict]) -> dict:
        """Embed + store verified images read from shared filesystem paths."""
        indexed, missing, unembeddable = 0, 0, 0
        batch = []
        for r in records:
            path = r.get("image_path") or ""
            if not path or not os.path.exists(path):
                missing += 1
                continue
            try:
                img = Image.open(path).convert("RGB")
            except Exception:
                missing += 1
                continue
            vec = dino_embedder.embed(img)
            if vec is None:
                unembeddable += 1
                continue
            batch.append({**r, "vector": vec})
            indexed += 1
        if batch:
            self.upsert_vectors(batch)
        return {"indexed": indexed, "missing": missing, "unembeddable": unembeddable,
                "embedding_version": EMBEDDING_VERSION, "dino_available": dino_embedder.available}

    # ------------------------------------------------------------- read path
    def count(self) -> int:
        try:
            return int(self.client().count(COLLECTION).count)
        except Exception:
            return 0

    def search(self, vector: np.ndarray, top_k: int = 8) -> list[dict]:
        c = self.client()
        vec = [float(v) for v in vector]
        try:
            res = c.query_points(COLLECTION, query=vec, limit=top_k, with_payload=True)
            hits = [{"id": p.id, "score": float(p.score), "payload": p.payload} for p in res.points]
        except Exception:
            raw = c.search(COLLECTION, query_vector=vec, limit=top_k, with_payload=True)
            hits = [{"id": str(p.id), "score": float(p.score), "payload": p.payload} for p in raw]
        return hits

    def query(self, vector: np.ndarray, top_k: int | None = None) -> dict:
        """Aggregate nearest verified images into per-pest evidence."""
        k = int(top_k or os.getenv("MEMORY_TOP_K", "8"))
        hits = self.search(vector, k)
        per_pest: dict[str, dict] = {}
        for h in hits:
            p = h["payload"] or {}
            pid = p.get("pest_id")
            if not pid:
                continue
            e = per_pest.setdefault(pid, {"pest_id": pid, "score": -1.0, "support_ids": [], "stages": set()})
            e["score"] = max(e["score"], h["score"])
            e["support_ids"].append(p.get("image_id"))
            if p.get("stage"):
                e["stages"].add(p["stage"])
        agg = sorted(
            ({"pest_id": e["pest_id"], "similarity": round(e["score"], 4),
              "support_count": len(e["support_ids"]), "support_ids": e["support_ids"][:5],
              "stages": sorted(e["stages"])} for e in per_pest.values()),
            key=lambda x: x["similarity"], reverse=True)
        top1 = agg[0] if agg else None
        top2 = agg[1] if len(agg) > 1 else None
        return {
            "matches": [{"image_id": (h["payload"] or {}).get("image_id"),
                         "pest_id": (h["payload"] or {}).get("pest_id"),
                         "stage": (h["payload"] or {}).get("stage"),
                         "similarity": h["score"],
                         "source": (h["payload"] or {}).get("source"),
                         "verification_status": (h["payload"] or {}).get("verification_status")}
                        for h in hits],
            "aggregated": agg[:5],
            "top1": top1, "top2": top2,
            "top1_score": top1["similarity"] if top1 else 0.0,
            "top2_score": top2["similarity"] if top2 else 0.0,
            "margin": round((top1["similarity"] if top1 else 0.0) - (top2["similarity"] if top2 else 0.0), 4),
            "support_count": top1["support_count"] if top1 else 0,
        }

    def stats(self) -> dict:
        counts: dict[str, int] = {}
        versions: dict[str, int] = {}
        try:
            c = self.client()
            nxt = None
            while True:
                pts, nxt = c.scroll(COLLECTION, limit=1000, with_payload=True, with_vectors=False, offset=nxt)
                for p in pts:
                    pay = p.payload or {}
                    counts[pay.get("pest_id") or "?"] = counts.get(pay.get("pest_id") or "?", 0) + 1
                    versions[pay.get("embedding_version") or "?"] = versions.get(pay.get("embedding_version") or "?", 0) + 1
                if not nxt:
                    break
        except Exception:
            pass
        return {"collection": COLLECTION, "total": sum(counts.values()), "per_pest": counts,
                "embedding_versions": versions, "embedding_version": EMBEDDING_VERSION,
                "dim": self.dim, "dino_available": dino_embedder.available}


def memory_evidence(crop: Image.Image, top_k: int | None = None) -> dict | None:
    """One-call evidence for the pipeline; None when the memory cannot speak
    (disabled, weights unavailable, or empty index) - the decision engine then
    simply ignores this signal source."""
    if os.getenv("MEMORY_ENABLED", "true").strip().lower() != "true":
        return None
    vec, emb_s = dino_embedder.embed_timed(crop)
    if vec is None:
        return None
    mem = VisualMemory()
    if mem.count() == 0:
        return None
    t0 = time.perf_counter()
    out = mem.query(vec, top_k)
    out["timings"] = {"embedding": emb_s, "qdrant_query": round(time.perf_counter() - t0, 3)}
    out["embedding_version"] = EMBEDDING_VERSION
    return out
