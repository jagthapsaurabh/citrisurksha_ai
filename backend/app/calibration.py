"""Calibration export builder (upgrade step 6).

Turns expert-reviewed detections (the authoritative labels) into labelled
calibration records carrying the full pipeline evidence snapshot that was
stored in `detections.ai_response` at prediction time. Raw/unreviewed farmer
uploads are never exported as labelled data.
"""
from __future__ import annotations


def build_calibration_record(row) -> dict | None:
    """row: backend Detection model instance. Returns None when the row is not
    an authoritative (expert-reviewed) detection."""
    ai = row.ai_response or {}
    reviewed = bool(getattr(row, "reviewed_by", None)) or row.admin_status in (
        "corrected", "approved_for_training")
    if not reviewed:
        return None
    label_pest = row.pest_id
    feat = ai
    signals = (ai.get("evidence") or {}).get("signals") or []
    memory = ai.get("memory") or {}
    clip = ai.get("clip") or {}
    cnn = [s for s in signals if s.get("source") == "cnn"]
    fused_top = (ai.get("candidates") or [{}])[0] if ai.get("candidates") else {}
    features = {
        "quality_acceptable": (ai.get("quality") or {}).get("acceptable", True),
        "failed_checks": (ai.get("quality") or {}).get("failed_checks", []),
        "detector_mode": (ai.get("detector") or {}).get("mode"),
        "detections": (ai.get("detector") or {}).get("detections", 0),
        "signals": signals,
        "memory": {
            "top1_pest": (memory.get("top1") or {}).get("pest_id"),
            "top1_score": memory.get("top1_score", 0.0),
            "top2_score": memory.get("top2_score", 0.0),
            "margin": memory.get("margin", 0.0),
            "support_count": memory.get("support_count", 0),
        } if memory else None,
        "clip": {
            "top1_pest": (clip.get("top1") or {}).get("pest_id"),
            "top1_score": (clip.get("top1") or {}).get("score", 0.0),
            "margin": clip.get("margin", 0.0),
        } if clip else None,
        "cnn": {"top1_pest": cnn[0].get("pest_id"), "top1_score": cnn[0].get("score", 0.0)} if cnn else None,
        "fused": {
            "top1_pest": fused_top.get("pest_id"),
            "top1_score": round(float(fused_top.get("score", 0.0)), 4),
            "margin": round(float(fused_top.get("score", 0.0)) - float((ai.get("candidates") or [None, {}])[1].get("score", 0.0)), 4)
            if len(ai.get("candidates") or []) > 1 else None,
        },
        "decision": ai.get("decision"),
        "confidence": ai.get("confidence"),
        "model_version": ai.get("model_version"),
    }
    return {
        "record_version": 1,
        "image_id": row.id,
        "label": {
            "pest_id": label_pest,
            "source": "expert_review",
            "reviewed_by": getattr(row, "reviewed_by", None),
            "reviewed_at": str(getattr(row, "reviewed_at", None)),
            "corrected_by_admin": bool(getattr(row, "corrected_by_admin", False)),
        },
        "features": features,
        "dataset_split": "calibration",
    }


def build_calibration_records(rows) -> list[dict]:
    out = []
    for r in rows:
        rec = build_calibration_record(r)
        if rec:
            out.append(rec)
    return out
