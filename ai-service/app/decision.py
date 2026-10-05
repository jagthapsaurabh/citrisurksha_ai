"""Decision engine (upgrade step 2/6-seed).

Fuses heterogeneous evidence (YOLO detection, legacy CNN, later DINOv2+Qdrant
and OpenCLIP) into one honest decision. The engine can and must say
"I don't know": supported decisions are identified / uncertain / unknown /
poor_image / no_pest_detected / non_target_image.

All weights & thresholds are configuration (env-overridable), never buried in
route code, so they can later be calibrated from validation data.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


DECISIONS = ["identified", "uncertain", "unknown", "poor_image", "no_pest_detected", "non_target_image"]


def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class ThresholdConfig:
    identify_min_conf: float = _f("DECIDE_IDENTIFY_MIN", 0.65)      # fused confidence to call it identified
    margin_min: float = _f("DECIDE_MARGIN_MIN", 0.08)              # top1-top2 margin below => uncertain
    negative_min: float = _f("DECIDE_NEGATIVE_MIN", 0.60)          # negative-class score above => no pest
    support_min: int = int(_f("DECIDE_SUPPORT_MIN", 1))            # verified neighbours needed (qdrant stage)
    source_weights: dict = field(default_factory=lambda: {
        "yolo": _f("W_YOLO", 0.45),
        "cnn": _f("W_CNN", 0.25),
        "dino_qdrant": _f("W_DINO", 0.20),
        "clip": _f("W_CLIP", 0.10),
    })

    @classmethod
    def load(cls) -> "ThresholdConfig":
        # Re-read env on every call so thresholds are tunable without restart
        # and unit-testable; later these can be calibrated from validation data.
        return cls(
            identify_min_conf=_f("DECIDE_IDENTIFY_MIN", 0.65),
            margin_min=_f("DECIDE_MARGIN_MIN", 0.08),
            negative_min=_f("DECIDE_NEGATIVE_MIN", 0.60),
            support_min=int(_f("DECIDE_SUPPORT_MIN", 1)),
            source_weights={
                "yolo": _f("W_YOLO", 0.45),
                "cnn": _f("W_CNN", 0.25),
                "dino_qdrant": _f("W_DINO", 0.20),
                "clip": _f("W_CLIP", 0.10),
            },
        )


@dataclass
class Signal:
    source: str          # yolo | cnn | dino_qdrant | clip
    pest_id: str | None  # None => negative / no-pest vote
    score: float
    weak: bool = False   # e.g. bootstrap CNN or fallback localiser


def fuse(signals: list[Signal], cfg: ThresholdConfig) -> tuple[list[dict], list[Signal]]:
    """Aggregate per-pest weighted scores across sources -> (sorted candidates, negative votes)."""
    per_pest: dict[str, dict] = {}
    neg_votes: list[Signal] = []
    for s in signals:
        if s.pest_id is None:
            neg_votes.append(s)
            continue
        w = cfg.source_weights.get(s.source, 0.1) * (0.5 if s.weak else 1.0)
        e = per_pest.setdefault(s.pest_id, {"pest_id": s.pest_id, "score": 0.0, "wsum": 0.0,
                                            "strong": False, "sources": {}})
        e["score"] += w * s.score
        e["wsum"] += w
        e["strong"] = e["strong"] or (not s.weak and s.score >= 0.5)
        e["sources"][s.source] = round(s.score, 3)
    # Normalise per pest by the weight of the sources that actually voted for
    # it, so one strong verified-memory match is not diluted by weak signals
    # elsewhere. Candidates backed ONLY by weak sources (bootstrap CNN, CLIP
    # zero-shot, fallback localiser) are ranked half as high - they can guide
    # and contradict, never out-rank strongly supported pests.
    for e in per_pest.values():
        base = e["score"] / e["wsum"] if e["wsum"] > 0 else 0.0
        e["base"] = round(base, 4)  # un-penalised evidence strength (for weak-only branch)
        e["score"] = round(base * (1.0 if e["strong"] else 0.5), 4)
        del e["wsum"]
    cand = sorted(per_pest.values(), key=lambda e: e["score"], reverse=True)
    return cand, neg_votes


def decide(quality: dict, candidates: list[dict], neg_votes: list[Signal],
           signals: list[Signal], cfg: ThresholdConfig | None = None,
           detector_meta: dict | None = None, support_count: int | None = None) -> dict:
    """Produce the final decision dict. Pure function - trivially unit-testable."""
    cfg = cfg or ThresholdConfig.load()
    detector_meta = detector_meta or {}
    evidence = {
        "signals": [{"source": s.source, "pest_id": s.pest_id, "score": round(s.score, 3), "weak": s.weak} for s in signals],
        "detector": {k: detector_meta.get(k) for k in ("mode", "detections", "tiled")},
        "quality_failed": quality.get("failed_checks", []),
    }

    if not quality.get("acceptable", False):
        failed = quality.get("failed_checks", [])
        decision = "poor_image" if "scene" not in failed else "non_target_image"
        if "corrupt" in failed:
            decision = "poor_image"
        return _out(decision, None, 0.0, [], evidence,
                    quality.get("advice") or "Please retake a clearer photo.")

    scene = (quality.get("checks") or {}).get("scene") or {}
    if not signals:
        if scene and not scene.get("ok", True):
            return _out("non_target_image", None, 0.0, [], evidence,
                        "The photo does not show a citrus plant or insect scene.")
        return _out("unknown", None, 0.0, [], evidence,
                    "No model produced evidence. The image needs expert review.")

    neg_best = max((s.score for s in neg_votes), default=0.0)
    if not candidates:
        if neg_best >= cfg.negative_min:
            return _out("no_pest_detected", None, round(neg_best, 3), [], evidence,
                        "Signals agree no citrus pest is present.")
        return _out("unknown", None, round(neg_best, 3), [], evidence,
                    "Evidence insufficient to identify a pest.")

    top1, top2 = candidates[0], (candidates[1] if len(candidates) > 1 else None)
    margin = top1["score"] - (top2["score"] if top2 else 0.0)

    # Cross-source disagreement on the winning pest => uncertain, always.
    strong = [s for s in signals if s.pest_id and not s.weak and s.score >= 0.5]
    distinct_winners = {s.pest_id for s in strong}
    disagreement = len(distinct_winners) > 1

    support_ok = support_count is None or support_count >= cfg.support_min
    weak_only = all(s.weak for s in signals if s.pest_id)

    if disagreement or margin < cfg.margin_min:
        reason = "Models disagree on the pest" if disagreement else "Top-1/top-2 margin too small"
        return _out("uncertain", top1["pest_id"], top1["score"], candidates, evidence, reason + "; sent for expert review.")

    if top1["score"] >= cfg.identify_min_conf and support_ok and not weak_only:
        return _out("identified", top1["pest_id"], top1["score"], candidates, evidence,
                    "Signals agree with sufficient confidence.")

    if weak_only and top1.get("base", top1["score"]) >= 0.3:
        return _out("uncertain", top1["pest_id"], top1["score"], candidates, evidence,
                    "Only preliminary (untrained) model evidence available; expert review recommended.")

    return _out("unknown", top1["pest_id"], top1["score"], candidates, evidence,
                "Confidence below identification threshold; needs expert review.")


def review_priority(decision: dict) -> float:
    """Active-learning seed: higher = label this one first. Base rules plus an
    OPTIONAL tuned boost from ACTIVE_LEARNING_WEIGHTS (a human-reviewed proposal
    produced by /active-learning/tune - never auto-applied)."""
    base = {"unknown": 0.9, "uncertain": 0.75, "poor_image": 0.2, "non_target_image": 0.1,
            "no_pest_detected": 0.15, "identified": 0.1}[decision["decision"]]
    conf = decision.get("confidence", 0.0)
    p = base + (0.25 * (1.0 - conf) if decision["decision"] in ("uncertain", "unknown") else 0.0)
    raw = os.getenv("ACTIVE_LEARNING_WEIGHTS", "").strip()
    if raw:
        try:
            import json as _json
            weights = _json.loads(raw)
            cands = decision.get("candidates") or []
            t1 = float(cands[0].get("score", 0.0)) if cands else 0.0
            margin = t1 - (float(cands[1].get("score", 0.0)) if len(cands) > 1 else 0.0)
            sigs = [s for s in (decision.get("evidence") or {}).get("signals", []) if s.get("pest_id")]
            strong = {s["pest_id"] for s in sigs if not s.get("weak") and s.get("score", 0) >= 0.5}
            indicators = {"low_conf": t1 < 0.55, "small_margin": margin < 0.08,
                          "disagreement": len(strong) > 1}
            p += sum(float(weights.get(k, 0.0)) for k, on in indicators.items() if on)
        except Exception:
            pass
    return round(min(1.0, p), 3)


def _out(decision: str, pest_id: str | None, confidence: float, candidates: list, evidence: dict, reason: str) -> dict:
    return {
        "decision": decision,
        "pest_id": pest_id,
        "confidence": round(float(confidence), 4),
        "candidates": candidates[:5],
        "evidence": evidence,
        "reason": reason,
    }
