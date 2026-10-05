"""Multi-stage detection pipeline (upgrade step 2).

quality -> YOLO11/OpenCV detector -> crop -> [legacy CNN signal] -> decision.
DINOv2/Qdrant/OpenCLIP join as extra signals in later steps; the pipeline is
written so adding a signal is a one-line append.

The output is backwards-compatible with the existing mobile contract
(Prediction schema) and ADDITIVE: new fields (decision, candidates, evidence,
quality, detector, timings, review_priority) are ignored by old clients.
PostgreSQL remains the source of truth for pest knowledge - nothing is
duplicated here.
"""
from __future__ import annotations

import hashlib
import os
import time

import numpy as np
from PIL import Image

from .decision import Signal, ThresholdConfig, decide, fuse, review_priority
from .detector import detector
from .quality import assess_quality, decode_image
from .model_registry import DEFAULT_CLASSES

NEGATIVE = "no-citrus-pest"


def pipeline_enabled() -> bool:
    return os.getenv("AI_ENGINE", "legacy").strip().lower() == "pipeline"


def _name_of(pest_id: str, classes: list[dict]) -> str:
    for c in classes:
        if c.get("id") == pest_id:
            return c.get("name") or pest_id
    return pest_id.replace("-", " ").title()


def _cnn_signal(img: Image.Image) -> tuple[Signal | None, dict]:
    """Legacy CNN as ONE evidence source (never the sole decision maker)."""
    try:
        from .ml import inference_engine
    except Exception:
        return None, {"mode": "unavailable"}
    meta = inference_engine.load_if_needed()
    trained = inference_engine.model is not None
    try:
        res = inference_engine.predict(img)
    except Exception:
        return None, {"mode": "error"}
    top_k = res.get("top_k") or []
    if not top_k:
        if res.get("is_citrus_pest") is False:
            return Signal("cnn", None, float(res.get("confidence", 0.5)), weak=not trained), {
                "mode": "trained" if trained else "bootstrap", "version": res.get("model_version")}
        return None, {"mode": "trained" if trained else "bootstrap", "version": res.get("model_version")}
    best = top_k[0]
    sig = Signal("cnn", best.get("pest_id"), float(best.get("confidence", 0.0)), weak=not trained)
    return sig, {"mode": "trained" if trained else "bootstrap", "version": res.get("model_version"),
                 "top_k": top_k[:5]}


def run_pipeline(content: bytes) -> dict:
    t_start = time.perf_counter()
    timings: dict = {}

    t0 = time.perf_counter()
    img_bgr, err = decode_image(content)
    quality = assess_quality(img_bgr) if img_bgr is not None else {
        "acceptable": False, "failed_checks": ["corrupt"], "checks": {},
        "advice": "The file could not be read as an image. Retake the photo.", "high_resolution": False}
    timings["opencv_quality"] = round(time.perf_counter() - t0, 3)

    signals: list[Signal] = []
    boxes, det_meta, crops = [], {}, []
    cnn_meta: dict = {}
    memory = None
    clip = None
    crop_img = None
    cfg = ThresholdConfig.load()

    if quality.get("acceptable"):
        t0 = time.perf_counter()
        boxes, det_meta = detector.detect(img_bgr)
        timings["detector"] = det_meta.get("seconds", round(time.perf_counter() - t0, 3))
        crops = detector.make_crops(img_bgr, boxes)

        # YOLO class votes (only meaningful once a pest-YOLO is trained).
        if det_meta.get("mode") == "yolo11":
            for b in boxes:
                signals.append(Signal("yolo", b["class_name"], b["confidence"]))
        elif boxes:
            # Fallback localiser found candidate regions: weak positive evidence
            # that *something* is present, without claiming a class.
            signals.append(Signal("yolo", None, 0.0, weak=True))

        t0 = time.perf_counter()
        crop_img = Image.fromarray(crops[0][:, :, ::-1]) if crops else Image.new("RGB", (64, 64))
        cnn_sig, cnn_meta = _cnn_signal(crop_img)
        timings["legacy_cnn"] = round(time.perf_counter() - t0, 3)
        if cnn_sig is not None:
            signals.append(cnn_sig)

        # DINOv2 + Qdrant visual memory (step 4). Conditional execution: only
        # when there is positive locality evidence and the memory can speak.
        if boxes or (cnn_sig is not None and cnn_sig.pest_id):
            t0 = time.perf_counter()
            try:
                from .memory import memory_evidence
                mem = memory_evidence(crop_img)
            except Exception:
                mem = None
            timings["dino_qdrant"] = round(time.perf_counter() - t0, 3)
            if mem:
                memory = mem
                t1 = mem.get("top1")
                if t1 and t1["similarity"] >= float(os.getenv("DINO_MIN_SIM", "0.25")):
                    signals.append(Signal("dino_qdrant", t1["pest_id"], t1["similarity"],
                                          weak=mem.get("support_count", 0) < cfg.support_min))
                elif mem.get("top1_score", 0.0) > 0:
                    # Visually novel vs the verified memory: weak negative vote.
                    signals.append(Signal("dino_qdrant", None, round((1.0 - mem["top1_score"]) * 0.6, 3), weak=True))

        # OpenCLIP zero-shot (step 5): independent secondary evidence, ALWAYS
        # weak - it can support or contradict, never decide on its own.
        if boxes or (cnn_sig is not None and cnn_sig.pest_id):
            t0 = time.perf_counter()
            try:
                from .clip_signal import clip_evidence
                clip = clip_evidence(crop_img)
            except Exception:
                clip = None
            timings["openclip"] = round(time.perf_counter() - t0, 3)
            if clip and clip.get("top1", {}).get("score", 0.0) > 0:
                signals.append(Signal("clip", clip["top1"]["pest_id"], clip["top1"]["score"], weak=True))

    candidates, neg_votes = fuse(signals, cfg)
    t0 = time.perf_counter()
    dec = decide(quality, candidates, neg_votes, signals, cfg,
                 detector_meta=det_meta, support_count=None)
    timings["decision"] = round(time.perf_counter() - t0, 4)

    # Active learning (step 11): remember what we could not identify so novel
    # pests surface as clusters of visually similar unknowns.
    if dec["decision"] in ("unknown", "uncertain") and crop_img is not None:
        try:
            from .active_learning import store_unknown
            from .embeddings import dino_embedder
            vec, _ = dino_embedder.embed_timed(crop_img)
            if vec is not None:
                store_unknown(vec, {
                    "image_sha": hashlib.sha256(content).hexdigest()[:16],
                    "top_candidate": dec.get("pest_id"),
                    "decision": dec["decision"],
                })
        except Exception:
            pass

    classes = DEFAULT_CLASSES
    top1 = dec["candidates"][0] if dec["candidates"] else None
    pest_id = dec["pest_id"]
    is_pest = dec["decision"] in ("identified", "uncertain") and pest_id is not None and pest_id != NEGATIVE

    conf = dec["confidence"]
    if dec["decision"] == "uncertain":
        conf = min(conf, 0.6)  # honest UX: below the backend's 0.65 low-confidence branch

    top_k = [
        {"pest_id": c["pest_id"], "pest_name": _name_of(c["pest_id"], classes), "confidence": c["score"]}
        for c in dec["candidates"]
    ] or ([{"pest_id": NEGATIVE, "pest_name": "No citrus pest detected", "confidence": max(0.0, 1 - conf)}] if not is_pest else [])

    severity = "none"
    if is_pest:
        severity = "high" if conf >= 0.85 else "medium" if conf >= 0.65 else "low"
        if dec["decision"] == "uncertain":
            severity = "preliminary"

    explanations = {
        "identified": "Multi-stage pipeline: detector + classifier evidence agree.",
        "uncertain": "Preliminary or conflicting AI evidence. An expert should review this scan.",
        "unknown": "The pipeline cannot identify this image. It has been queued for expert review.",
        "poor_image": quality.get("advice") or "Please retake a clearer photo.",
        "no_pest_detected": "No citrus pest detected. Please upload a clear citrus pest, insect or plant-damage image.",
        "non_target_image": "This does not look like a citrus plant/pest photo. Please photograph the leaf, fruit or insect.",
    }

    dec["review_priority"] = review_priority(dec)
    timings["total"] = round(time.perf_counter() - t_start, 3)

    return {
        # ---- existing mobile contract (unchanged semantics) ----
        "is_citrus_pest": is_pest,
        "pest_id": pest_id if is_pest else None,
        "pest_name": _name_of(pest_id, classes) if is_pest else (
            "No citrus pest detected" if dec["decision"] == "no_pest_detected" else "Unknown - needs expert review"),
        "confidence": round(conf, 4),
        "severity_level": severity,
        "stage": "unknown" if is_pest else None,
        "model_version": f"pipeline-v1|cnn:{cnn_meta.get('version', 'none')}|det:{det_meta.get('mode', 'none')}",
        "top_k": top_k,
        "explanation": explanations.get(dec["decision"], dec["reason"]),
        "recommendation": dec["reason"],
        # ---- additive pipeline fields (ignored by old clients) ----
        "decision": dec["decision"],
        "candidates": dec["candidates"],
        "evidence": dec["evidence"],
        "quality": {k: quality.get(k) for k in ("acceptable", "failed_checks", "advice", "high_resolution")},
        "detector": det_meta,
        "review_priority": dec["review_priority"],
        "memory": memory,
        "clip": clip,
        "timings": timings,
    }
