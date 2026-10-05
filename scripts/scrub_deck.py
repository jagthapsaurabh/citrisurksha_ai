"""Board-deck confidentiality scrub: removes paid/free/open-source API framing and
internal model names. Capability language only; ownership messages kept.

  pip install python-pptx
  python3 scripts/scrub_deck.py
"""
from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation

DECK = Path(__file__).resolve().parents[1] / "docs" / "pitch" / "CitriSuraksha_AI_Board_Pitch.pptx"

EXACT = [
    ("YOLO11 detector\nbox + crop (fallback localiser)", "Pest detector\nbox + crop"),
    ("DINOv2 + Qdrant\nverified-image memory", "Visual memory\nverified-image similarity"),
    ("OpenCLIP zero-shot\nsecondary, always weak", "Cross-check signal\nsecondary, always weak"),
    ("Verified classification images start YOLO11 box training (full-image bootstrap boxes, clearly labelled).",
     "Verified classification images start detector box training (bootstrap boxes, clearly labelled)."),
    ("Unidentified crops are DINOv2-embedded and clustered; coherent clusters surface as CANDIDATE NEW CLASS before anyone has named them.",
     "Unidentified crops are embedded and clustered; coherent clusters surface as CANDIDATE NEW CLASS before anyone has named them."),
    ("Open-source backbones (MobileNetV3 etc.) — selectable per training run; custom pests can be added.",
     "Model profiles are selectable per training run; custom pests can be added."),
    ("PyTorch + TorchVision, open-source architectures (MobileNetV3 / EfficientNet family) — no paid APIs, no per-scan cost.",
     "In-house vision engine, trained only on our own verified dataset."),
    ("AI service — real PyTorch training pipeline, model registry, strict 21-class coverage gates.",
     "AI service — in-house training pipeline, model registry, strict 21-class coverage gates."),
    ("Zero paid AI APIs — full IP & data ownership",
     "Full IP & data ownership — every model trained in-house"),
    ("PyTorch + TorchVision\n21-class pest classifier\nOpen-source models only",
     "In-house vision engine\n21-class pest classifier\nTrained on our verified data"),
    ("Zero paid AI", "Full data ownership"),
    ("Open-source PyTorch/TorchVision/DINOv2/OpenCLIP; all data and models on our servers.",
     "Every image, label and model stays on our own servers."),
    ("Open-source only", "Deployment flexibility"),
    ("Upload caps, traversal blocked, auth enforced, no tracked secrets, leak-free diagnostics.",
     "Upload caps, traversal blocked, auth enforced, no tracked secrets, clean diagnostics."),
]

RULES = [
    (re.compile(r"No paid AI APIs\..*"), "The vision model is trained in-house on our own verified dataset — full data ownership."),
    (re.compile(r"FastAPI \+ PostgreSQL \+ PyTorch vision service"), "FastAPI + PostgreSQL + in-house vision service"),
    (re.compile(r"open[- ]source", re.I), "in-house"),
    (re.compile(r"\bYOLO11\b"), "AI detector"),
    (re.compile(r"\bDINOv2(?:\s*\+\s*Qdrant)?\b"), "visual memory"),
    (re.compile(r"\bQdrant\b"), "vector index"),
    (re.compile(r"\bOpenCLIP\b"), "cross-check"),
    (re.compile(r"\bPyTorch(?:\s*/\s*TorchVision)?\b"), "our vision engine"),
    (re.compile(r"\bTorchVision\b"), "vision engine"),
    (re.compile(r"MobileNetV3[^)\n]*"), "on-device profile"),
    (re.compile(r"\bEfficientNet[^)\n]*"), "accuracy profile"),
    (re.compile(r"\bResNet\b"), "baseline profile"),
    (re.compile(r"paid AI[^.\n]*", re.I), "in-house AI"),
    (re.compile(r"\bfree (?:AI )?APIs?", re.I), "in-house AI"),
]


def scrub_text(t: str) -> str:
    for old, new in EXACT:
        t = t.replace(old, new)
    for rx, new in RULES:
        t = rx.sub(new, t)
    return t


def main() -> int:
    prs = Presentation(str(DECK))
    changed = 0
    for s in prs.slides:
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            for p in sh.text_frame.paragraphs:
                full = "".join(r.text for r in p.runs)
                if not full:
                    continue
                new = scrub_text(full)
                if new != full:
                    changed += 1
                    runs = p.runs
                    runs[0].text = new
                    for r in runs[1:]:
                        r.text = ""
    prs.save(str(DECK))
    print(f"scrubbed paragraphs: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
