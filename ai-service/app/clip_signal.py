"""OpenCLIP zero-shot secondary signal (upgrade step 5).

OpenCLIP is an INDEPENDENT, SECONDARY piece of evidence: configurable text
prompts per known citrus pest are compared against the detected crop. It is
deliberately fed to the decision engine as a *weak* signal - zero-shot CLIP is
not reliable enough for fine-grained pest species to ever act as the primary
classifier, and the final decision never simply follows the highest score
(cross-source disagreement instead produces `uncertain`).

No paid AI API: OpenCLIP + the open "openai" pretrained weights are open source.
"""
from __future__ import annotations

import json
import os
import time

import numpy as np
from PIL import Image

try:
    import torch
except Exception:  # pragma: no cover
    torch = None

try:
    import open_clip
except Exception:  # pragma: no cover
    open_clip = None

from .model_registry import DEFAULT_CLASSES

DEFAULT_TEMPLATES = [
    "a photo of {name} on a citrus leaf",
    "close-up of {name} insect on an orange tree",
    "{name} pest damage on citrus plant",
    "a citrus leaf infested with {name}",
]
NEGATIVE_PROMPTS = [
    "a photo of a healthy green citrus leaf with no pest",
    "a clean orange tree leaf without insects or damage",
]


def clip_enabled() -> bool:
    return os.getenv("CLIP_ENABLED", "true").strip().lower() == "true" and open_clip is not None and torch is not None


def clip_model_name() -> tuple[str, str]:
    return os.getenv("CLIP_MODEL", "ViT-B-32"), os.getenv("CLIP_PRETRAINED", "openai")


class ClipScorer:
    """Cached OpenCLIP model + cached per-class prompt tokenization."""

    def __init__(self) -> None:
        self._model = None
        self._preprocess = None
        self._tokenizer = None
        self._failed = False
        self._text_cache: dict = {}

    def _load(self):
        if self._model is not None or self._failed or not clip_enabled():
            return self._model
        name, pretrained = clip_model_name()
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(name, pretrained=pretrained)
            model.eval()
            self._model, self._preprocess = model, preprocess
            self._tokenizer = open_clip.get_tokenizer(name)
        except Exception:
            self._model, self._failed = None, True
        return self._model

    @property
    def available(self) -> bool:
        return self._load() is not None

    # ------------------------------------------------------------ prompts
    @staticmethod
    def prompts_for(classes: list[dict]) -> tuple[list[str], list[str], list[int]]:
        """Return (class_ids, prompts, per_class_counts) in parallel order."""
        override = {}
        path = os.getenv("CLIP_PROMPTS_FILE", "").strip()
        if not path:
            bundled = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "config", "clip_prompts.json")
            if os.path.exists(bundled):
                path = bundled
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    override = json.load(f)
            except Exception:
                override = {}
        ids, prompts, counts = [], [], []
        for c in classes:
            pid = c.get("id")
            name = c.get("name") or pid
            ids.append(pid)
            if pid == "no-citrus-pest":
                plist = NEGATIVE_PROMPTS
            else:
                plist = [t.format(name=name.lower()) for t in (override.get(pid) or DEFAULT_TEMPLATES)]
            prompts += plist
            counts.append(len(plist))
        return ids, prompts, counts

    def _text_features(self, key: tuple, prompts: list[str], counts: list[int]):
        if key not in self._text_cache:
            tok = self._tokenizer(prompts)
            with torch.no_grad():
                f = self._model.encode_text(tok)
                f = f / f.norm(dim=-1, keepdim=True)
            per_class, idx = [], 0
            for n in counts:
                vec = f[idx:idx + n].mean(dim=0)
                per_class.append(vec / vec.norm())
                idx += n
            self._text_cache[key] = torch.stack(per_class)
        return self._text_cache[key]

    # ------------------------------------------------------------ scoring
    def score(self, image: Image.Image, classes: list[dict] | None = None) -> dict | None:
        model = self._load()
        if model is None:
            return None
        classes = classes or DEFAULT_CLASSES
        ids, prompts, counts = self.prompts_for(classes)
        key = (tuple(ids), tuple(prompts))
        t0 = time.perf_counter()
        with torch.no_grad():
            img = self._preprocess(image.convert("RGB")).unsqueeze(0)
            vf = model.encode_image(img)
            vf = vf / vf.norm(dim=-1, keepdim=True)
            tf = self._text_features(key, prompts, counts)
            logits = (vf @ tf.T).squeeze(0) * float(self._model.logit_scale.exp())
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
        order = probs.argsort()[::-1]
        scores = {ids[i]: round(float(probs[i]), 4) for i in range(len(ids))}
        top1, top2 = ids[int(order[0])], (ids[int(order[1])] if len(ids) > 1 else None)
        return {
            "model": clip_model_name()[0],
            "scores": scores,
            "top1": {"pest_id": top1, "score": round(float(probs[int(order[0])]), 4)},
            "top2": {"pest_id": top2, "score": round(float(probs[int(order[1])]), 4) if top2 else 0.0},
            "margin": round(float(probs[int(order[0])] - probs[int(order[1])]), 4) if top2 else 0.0,
            "seconds": round(time.perf_counter() - t0, 3),
        }


clip_scorer = ClipScorer()


def clip_evidence(crop: Image.Image, classes: list[dict] | None = None) -> dict | None:
    """One-call evidence for the pipeline; None when disabled/unavailable."""
    if not clip_enabled():
        return None
    return clip_scorer.score(crop, classes)
