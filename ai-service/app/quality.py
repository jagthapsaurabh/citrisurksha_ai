"""OpenCV image-quality gate (upgrade step 2).

Runs BEFORE any model inference. Poor images never produce an unreliable pest
prediction - the decision engine turns them into `poor_image` with friendly
retake advice. All thresholds are configurable via environment variables.
"""
from __future__ import annotations

import os

import cv2
import numpy as np


def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def quality_config() -> dict:
    return {
        "min_short_side": int(_f("QUALITY_MIN_SHORT_SIDE", 200)),
        "max_long_side": int(_f("QUALITY_MAX_LONG_SIDE", 8000)),
        "blur_threshold": _f("QUALITY_BLUR_THRESHOLD", 40.0),   # Laplacian variance at 512px
        "dark_threshold": _f("QUALITY_DARK_THRESHOLD", 25.0),   # mean gray below = too dark
        "bright_threshold": _f("QUALITY_BRIGHT_THRESHOLD", 240.0),
        "contrast_threshold": _f("QUALITY_CONTRAST_THRESHOLD", 12.0),  # gray std below = flat
        "texture_threshold": _f("QUALITY_TEXTURE_THRESHOLD", 0.002),   # Canny edge ratio
    }


def decode_image(content: bytes):
    """Return (bgr_ndarray|None, error_string|None). Rejects corrupt/undecodable files."""
    if not content or len(content) < 100:
        return None, "empty-or-tiny"
    arr = np.frombuffer(content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None, "undecodable"
    return img, None


def assess_quality(img: np.ndarray) -> dict:
    """Assess a decoded BGR image. Pure OpenCV/numpy, no models."""
    cfg = quality_config()
    h, w = img.shape[:2]
    checks: dict = {}
    checks["resolution"] = {
        "width": int(w), "height": int(h),
        "ok": (min(h, w) >= cfg["min_short_side"] and max(h, w) <= cfg["max_long_side"]),
        "advice": None if (min(h, w) >= cfg["min_short_side"]) else "Photo is too small. Move closer and use the rear camera.",
    }

    # Work on a capped copy so metrics are scale-stable and cheap.
    scale = min(1.0, 512.0 / max(h, w))
    small = img if scale >= 1.0 else cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    mean_lum = float(gray.mean())
    checks["brightness"] = {
        "mean": round(mean_lum, 1),
        "ok": cfg["dark_threshold"] <= mean_lum <= cfg["bright_threshold"],
        "advice": "Image is too dark. Retake in daylight." if mean_lum < cfg["dark_threshold"]
        else ("Image is over-exposed. Retake avoiding direct glare." if mean_lum > cfg["bright_threshold"] else None),
    }

    contrast = float(gray.std())
    checks["contrast"] = {
        "std": round(contrast, 1), "ok": contrast >= cfg["contrast_threshold"],
        "advice": "Image looks flat/washed out. Retake closer with the pest centered.",
    }

    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    checks["blur"] = {
        "laplacian_var": round(blur, 1), "ok": blur >= cfg["blur_threshold"],
        "advice": "Image is blurry. Hold the phone steady and tap to focus on the pest.",
    }

    edges = cv2.Canny(gray, 60, 140)
    texture = float((edges > 0).mean())
    checks["texture"] = {
        "edge_ratio": round(texture, 4), "ok": texture >= cfg["texture_threshold"],
        "advice": "Image has no usable detail (blank surface or document). Photograph the plant/pest.",
    }

    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hh, ss, vv = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    green_ratio = float(((hh >= 25) & (hh <= 90) & (ss > 40) & (vv > 40)).mean())
    brown_ratio = float(((hh >= 8) & (hh <= 25) & (ss > 40) & (vv > 40)).mean())
    checks["scene"] = {
        "green_ratio": round(green_ratio, 3), "brown_ratio": round(brown_ratio, 3),
        "ok": (green_ratio + brown_ratio) >= 0.03,
        "advice": "This does not look like a plant/pest photo. Photograph the citrus leaf, fruit or insect.",
    }

    failures = [k for k, v in checks.items() if not v["ok"]]
    advices = [v["advice"] for k, v in checks.items() if not v["ok"] and v.get("advice")]
    acceptable = len(failures) == 0
    return {
        "acceptable": acceptable,
        "failed_checks": failures,
        "advice": " ".join(advices[:2]) if advices else None,
        "checks": checks,
        "high_resolution": bool(max(h, w) >= 1600),
    }


def assess_bytes(content: bytes) -> dict:
    img, err = decode_image(content)
    if img is None:
        return {
            "acceptable": False,
            "failed_checks": ["corrupt"],
            "advice": "The file could not be read as an image. Retake the photo.",
            "checks": {"corrupt": {"ok": False, "error": err}},
            "high_resolution": False,
        }
    return assess_quality(img)
