"""YOLO11 insect detector with OpenCV fallback localisation (upgrade step 2).

Design rules honoured here:
- YOLO11s-sized models first; everything configurable (model, imgsz, conf, iou,
  device, batch).
- The detector is cached once loaded (no per-request weight loading).
- When no trained pest-YOLO weights are configured yet, an honest OpenCV
  fallback proposes candidate insect regions (clearly labelled
  `opencv_fallback`) so the pipeline stays usable pre-training.
- Tiled inference ONLY for very high-resolution images where small insects
  would otherwise be lost; never otherwise.
"""
from __future__ import annotations

import os
import time

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional until installed
    YOLO = None


def detector_config() -> dict:
    return {
        "weights": os.getenv("YOLO_WEIGHTS", "").strip(),          # path to trained yolo11 pest weights
        "model": os.getenv("YOLO_MODEL", "yolo11s.pt"),            # architecture hint for future training
        "imgsz": int(os.getenv("YOLO_IMGSZ", "640")),
        "conf": float(os.getenv("YOLO_CONF", "0.25")),
        "iou": float(os.getenv("YOLO_IOU", "0.45")),
        "device": os.getenv("YOLO_DEVICE", "cpu"),
        "batch": int(os.getenv("YOLO_BATCH", "1")),
        "tiling": os.getenv("DETECTOR_TILING", "true").lower() == "true",
        "tile_trigger": int(os.getenv("DETECTOR_TILE_TRIGGER", "1600")),
    }


class Detector:
    """Cached YOLO11 detector with OpenCV fallback crop proposal."""

    def __init__(self) -> None:
        self._model = None
        self._loaded_weights = None

    # ------------------------------------------------------------------ yolo
    def _load_yolo(self, cfg: dict):
        weights = cfg["weights"]
        if not weights:
            # No explicit weights configured: adopt a deployed YOLO detector if
            # the governed registry has one in production (architecture yolo*).
            try:
                from .model_registry import active_model
                meta = active_model()
                if str(meta.get("architecture", "")).lower().startswith("yolo"):
                    cand = meta.get("checkpoint_path")
                    if cand and os.path.exists(cand):
                        weights = cand
            except Exception:
                weights = ""
        if not weights or YOLO is None or not os.path.exists(weights):
            return None
        if self._model is not None and self._loaded_weights == weights:
            return self._model
        try:
            self._model = YOLO(weights)
            self._loaded_weights = weights
            return self._model
        except Exception:
            self._model = None
            self._loaded_weights = None
            return None

    def _yolo_detect(self, model, img: np.ndarray, cfg: dict) -> list[dict]:
        res = model.predict(img, imgsz=cfg["imgsz"], conf=cfg["conf"], iou=cfg["iou"],
                            device=cfg["device"], batch=cfg["batch"], verbose=False)
        out = []
        if not res:
            return out
        r = res[0]
        names = r.names or {}
        boxes = r.boxes
        if boxes is None:
            return out
        for i in range(len(boxes)):
            x1, y1, x2, y2 = [float(v) for v in boxes.xyxy[i].tolist()]
            out.append({
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "confidence": round(float(boxes.conf[i]), 4),
                "class_id": int(boxes.cls[i]),
                "class_name": str(names.get(int(boxes.cls[i]), "pest")),
            })
        return out

    # ------------------------------------------------- opencv fallback localiser
    @staticmethod
    def _opencv_boxes(img: np.ndarray) -> list[dict]:
        """Propose candidate insect/damage regions without a trained model.

        Insects & damage on citrus usually contrast with the green canopy
        (brown/yellow/white/silvery). We segment non-green salient blobs and
        keep contours of plausible insect size. Honest fallback: boxes carry
        class_name 'insect-candidate'.
        """
        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hh, ss, vv = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        green = ((hh >= 25) & (hh <= 90) & (ss > 40) & (vv > 40))
        salient = (~green & (vv > 50) & (ss > 25)).astype(np.uint8) * 255
        salient = cv2.morphologyEx(salient, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        contours, _ = cv2.findContours(salient, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        area = h * w
        for c in sorted(contours, key=cv2.contourArea, reverse=True)[:4]:
            a = cv2.contourArea(c)
            if a < 0.002 * area or a > 0.6 * area:
                continue
            x, y, bw, bh = cv2.boundingRect(c)
            boxes.append({"x1": float(x), "y1": float(y), "x2": float(x + bw), "y2": float(y + bh),
                          "confidence": 0.35, "class_id": 0, "class_name": "insect-candidate"})
        return boxes

    # ------------------------------------------------------------------ tiling
    @staticmethod
    def _nms(boxes: list[dict], iou_thr: float = 0.5) -> list[dict]:
        boxes = sorted(boxes, key=lambda b: b["confidence"], reverse=True)
        keep = []
        for b in boxes:
            if all(_iou(b, k) < iou_thr for k in keep):
                keep.append(b)
        return keep

    def _tiled_detect(self, detect_fn, img: np.ndarray) -> list[dict]:
        h, w = img.shape[:2]
        th, tw = h // 2, w // 2
        oh, ow = int(th * 0.15), int(tw * 0.15)
        tiles = [
            (0, 0), (0, tw - ow), (th - oh, 0), (th - oh, tw - ow),
        ]
        out: list[dict] = []
        for ty, tx in tiles:
            sub = img[ty:ty + th + oh, tx:tx + tw + ow]
            for b in detect_fn(sub):
                out.append({**b, "x1": b["x1"] + tx, "y1": b["y1"] + ty,
                            "x2": b["x2"] + tx, "y2": b["y2"] + ty})
        return self._nms(out)

    # ------------------------------------------------------------------ entry
    def detect(self, img: np.ndarray) -> tuple[list[dict], dict]:
        """Return (boxes, meta). meta.mode: yolo11 | opencv_fallback."""
        cfg = detector_config()
        t0 = time.perf_counter()
        h, w = img.shape[:2]
        use_tiling = cfg["tiling"] and max(h, w) > cfg["tile_trigger"]

        model = self._load_yolo(cfg)
        if model is not None:
            fn = lambda im: self._yolo_detect(model, im, cfg)
            boxes = self._tiled_detect(fn, img) if use_tiling else fn(img)
            mode = "yolo11"
        else:
            boxes = self._tiled_detect(self._opencv_boxes, img) if use_tiling else self._opencv_boxes(img)
            mode = "opencv_fallback"

        meta = {
            "mode": mode,
            "model": cfg["weights"] if mode == "yolo11" else None,
            "architecture": cfg["model"],
            "imgsz": cfg["imgsz"], "conf": cfg["conf"], "iou": cfg["iou"],
            "device": cfg["device"], "tiled": bool(use_tiling),
            "detections": len(boxes),
            "seconds": round(time.perf_counter() - t0, 3),
            "yolo_available": YOLO is not None,
        }
        return boxes, meta

    # ------------------------------------------------------------------ crops
    @staticmethod
    def make_crops(img: np.ndarray, boxes: list[dict], pad: float = 0.12) -> list[np.ndarray]:
        """Padded crops for each box; centre crop when nothing was detected."""
        h, w = img.shape[:2]
        crops = []
        for b in boxes:
            bw, bh = b["x2"] - b["x1"], b["y2"] - b["y1"]
            x1 = max(0, int(b["x1"] - bw * pad)); y1 = max(0, int(b["y1"] - bh * pad))
            x2 = min(w, int(b["x2"] + bw * pad)); y2 = min(h, int(b["y2"] + bh * pad))
            if x2 - x1 < 24 or y2 - y1 < 24:
                continue
            crops.append(img[y1:y2, x1:x2])
        if not crops:
            ch, cw = int(h * 0.68), int(w * 0.68)
            y1, x1 = (h - ch) // 2, (w - cw) // 2
            crops.append(img[y1:y1 + ch, x1:x1 + cw])
        return crops


def _iou(a: dict, b: dict) -> float:
    ix1, iy1 = max(a["x1"], b["x1"]), max(a["y1"], b["y1"])
    ix2, iy2 = min(a["x2"], b["x2"]), min(a["y2"], b["y2"])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    ua = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"]) + (b["x2"] - b["x1"]) * (b["y2"] - b["y1"]) - inter
    return inter / ua if ua > 0 else 0.0


detector = Detector()
