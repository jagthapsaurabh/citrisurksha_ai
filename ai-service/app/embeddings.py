"""DINOv2 visual embeddings (upgrade step 4).

Pretrained DINOv2 (ViT-S/14) is used strictly as an embedding model for
fine-grained visual similarity - never as a detector or classifier. Weights are
loaded once and cached; if they cannot be loaded (offline box, hub blocked, or
DINOV2_ENABLED=false) the pipeline degrades gracefully and simply omits the
DINOv2/Qdrant signal instead of failing or faking.

No paid AI API: DINOv2 weights are Meta's openly released research weights
fetched from the official GitHub repo and cached locally.
"""
from __future__ import annotations

import os
import time

import numpy as np
from PIL import Image

try:
    import torch
    from torchvision import transforms
except Exception:  # pragma: no cover
    torch = None
    transforms = None

EMBEDDING_VERSION = "dinov2-vits14-v1"
EMBEDDING_DIM = 384  # ViT-S/14 CLS token


def dino_enabled() -> bool:
    return os.getenv("DINOV2_ENABLED", "true").strip().lower() == "true" and torch is not None


class DinoEmbedder:
    """Cached pretrained DINOv2 embedder."""

    def __init__(self) -> None:
        self._model = None
        self._failed = False

    def _load(self):
        if self._model is not None or self._failed or not dino_enabled():
            return self._model
        try:
            hub_dir = os.getenv("DINO_HUB_DIR", "").strip() or None
            if hub_dir:
                torch.hub.set_dir(hub_dir)
            self._model = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14")
            self._model.eval()
        except Exception:
            self._model = None
            self._failed = True
        return self._model

    @property
    def available(self) -> bool:
        return self._load() is not None

    def transform(self):
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def embed(self, image: Image.Image) -> np.ndarray | None:
        """Unit-norm CLS embedding (384-d) or None when unavailable."""
        model = self._load()
        if model is None:
            return None
        with torch.no_grad():
            x = self.transform()(image.convert("RGB")).unsqueeze(0)
            v = model(x).squeeze(0).cpu().numpy().astype("float32")
        n = float(np.linalg.norm(v))
        return v / n if n > 0 else None

    def embed_timed(self, image: Image.Image) -> tuple[np.ndarray | None, float]:
        t0 = time.perf_counter()
        vec = self.embed(image)
        return vec, round(time.perf_counter() - t0, 3)


dino_embedder = DinoEmbedder()
