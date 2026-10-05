"""Calibration dataset format + threshold/weight proposals (upgrade step 6).

The pipeline stores its full evidence trail in every prediction (signals per
source, memory top-1/top-2/margin/support, clip scores, quality checks, fused
scores, decision). The backend exports reviewed detections as labelled
calibration records; this module turns them into PROPOSALS for decision-engine
weights and thresholds.

Golden rule: nothing is applied automatically. Proposals are written to a JSON
file for a human to review and copy into the environment/config.
"""
from __future__ import annotations

import json
import statistics
from typing import Any

RECORD_VERSION = 1

REQUIRED_FEATURE_KEYS = ["quality_acceptable", "signals", "fused", "decision"]


def make_record(image_id: str, label_pest_id: str | None, features: dict,
                reviewed_by: str | None = None, reviewed_at: str | None = None,
                dataset_split: str = "calibration") -> dict:
    return {
        "record_version": RECORD_VERSION,
        "image_id": str(image_id),
        "label": {"pest_id": label_pest_id, "source": "expert_review",
                  "reviewed_by": reviewed_by, "reviewed_at": reviewed_at},
        "features": features,
        "dataset_split": dataset_split,
    }


def validate_record(rec: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(rec, dict):
        return False, ["record must be an object"]
    if rec.get("record_version") != RECORD_VERSION:
        errors.append(f"record_version must be {RECORD_VERSION}")
    if not rec.get("image_id"):
        errors.append("image_id required")
    label = rec.get("label") or {}
    if "pest_id" not in label:
        errors.append("label.pest_id required (may be null for no-pest)")
    if label.get("source") != "expert_review":
        errors.append("label.source must be 'expert_review' (raw farmer uploads are never authoritative)")
    feat = rec.get("features") or {}
    for k in REQUIRED_FEATURE_KEYS:
        if k not in feat:
            errors.append(f"features.{k} required")
    return (not errors), errors


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _p(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def suggest_thresholds(records: list[dict], defaults: dict | None = None) -> dict:
    """Propose DECIDE_* thresholds and W_* source weights from labelled records.

    Returns a proposal dict; `applied` is always False - a human must approve.
    """
    defaults = defaults or {"DECIDE_IDENTIFY_MIN": 0.65, "DECIDE_MARGIN_MIN": 0.08,
                            "W_YOLO": 0.45, "W_CNN": 0.25, "W_DINO": 0.20, "W_CLIP": 0.10}
    usable = []
    for rec in records:
        ok, _ = validate_record(rec)
        if not ok:
            continue
        feat = rec["features"]
        if not feat.get("quality_acceptable", False):
            continue
        fused = feat.get("fused") or {}
        if not fused.get("top1_pest") and rec["label"]["pest_id"]:
            continue
        usable.append(rec)

    stats: dict[str, Any] = {"records_total": len(records), "records_usable": len(usable)}
    if not usable:
        return {"applied": False, "proposed": defaults, "stats": stats,
                "note": "No usable labelled records; defaults kept."}

    def is_correct(rec: dict) -> bool:
        fused = rec["features"]["fused"]
        label = rec["label"]["pest_id"]
        if label is None:
            return rec["features"]["decision"] in ("no_pest_detected", "non_target_image")
        return fused.get("top1_pest") == label

    correct = [r for r in usable if is_correct(r)]
    wrong = [r for r in usable if not is_correct(r)]
    stats["correct"] = len(correct)
    stats["wrong"] = len(wrong)

    # ---- per-source separability -> weight proposal
    source_key = {"yolo": "W_YOLO", "cnn": "W_CNN", "dino_qdrant": "W_DINO", "clip": "W_CLIP"}
    sep: dict[str, float] = {}
    for src, wkey in source_key.items():
        same, diff = [], []
        for r in usable:
            label = r["label"]["pest_id"]
            sigs = [s for s in r["features"]["signals"] if s.get("source") == src and s.get("pest_id")]
            if not sigs:
                continue
            top = max(sigs, key=lambda s: s.get("score", 0))
            (same if top["pest_id"] == label else diff).append(top.get("score", 0.0))
        m_same = statistics.mean(same) if same else 0.0
        m_diff = statistics.mean(diff) if diff else 0.0
        sep[src] = m_same - m_diff
        stats[f"sep_{src}"] = round(sep[src], 4)
    positive = {k: max(0.02, v) for k, v in sep.items()}
    total = sum(positive.values())
    proposed_weights = {source_key[k]: round(0.5 * defaults[source_key[k]] + 0.5 * (v / total), 3)
                        for k, v in positive.items()}
    # blend with defaults (50/50) until the dataset is large enough to trust fully
    if len(usable) >= 100:
        proposed_weights = {source_key[k]: round(v / total, 3) for k, v in positive.items()}

    # ---- identify threshold from fused score distributions
    sc = [r["features"]["fused"].get("top1_score", 0.0) for r in correct]
    sw = [r["features"]["fused"].get("top1_score", 0.0) for r in wrong]
    proposed = dict(defaults)
    proposed.update(proposed_weights)
    if sc and sw:
        lo, hi = _p(sc, 0.25), _p(sw, 0.75)
        if lo > hi:
            proposed["DECIDE_IDENTIFY_MIN"] = round(_clamp((lo + hi) / 2, 0.5, 0.95), 3)
        stats["fused_p25_correct"] = round(lo, 3)
        stats["fused_p75_wrong"] = round(hi, 3)
    mc = [r["features"]["fused"].get("margin", 0.0) for r in correct if r["features"]["fused"].get("margin") is not None]
    mw = [r["features"]["fused"].get("margin", 0.0) for r in wrong if r["features"]["fused"].get("margin") is not None]
    if mc and mw:
        lo, hi = _p(mc, 0.25), _p(mw, 0.75)
        if lo > hi:
            proposed["DECIDE_MARGIN_MIN"] = round(_clamp((lo + hi) / 2, 0.02, 0.4), 3)

    return {"applied": False, "proposed": proposed, "stats": stats,
            "note": "Proposal only. Review stats, then copy values into env/config."}


def write_proposal(proposal: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proposal, f, indent=2)
