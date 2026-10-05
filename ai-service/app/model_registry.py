import json
import os
from datetime import datetime
from pathlib import Path

MODEL_STORE = os.getenv("MODEL_STORE", "/app/model-store")
ACTIVE_MODEL_FILE = os.path.join(MODEL_STORE, "active_model.json")

DEFAULT_CLASSES = [
    {"id": "no-citrus-pest", "name": "No citrus pest detected"},
    {"id": "citrus-psyllid", "name": "Asian citrus psyllid"},
    {"id": "citrus-leaf-miner", "name": "Citrus leaf miner"},
    {"id": "citrus-blackfly", "name": "Citrus blackfly"},
    {"id": "citrus-whitefly", "name": "Citrus whitefly"},
    {"id": "brown-citrus-aphid", "name": "Brown citrus aphid"},
    {"id": "cotton-aphid", "name": "Cotton aphid"},
    {"id": "citrus-mealybug", "name": "Citrus mealybug"},
    {"id": "california-red-scale", "name": "California red scale"},
    {"id": "purple-scale", "name": "Purple scale"},
    {"id": "green-shield-scale", "name": "Green shield scale"},
    {"id": "citrus-red-mite", "name": "Citrus red mite"},
    {"id": "oriental-spider-mite", "name": "Oriental spider mite"},
    {"id": "citrus-rust-mite", "name": "Citrus rust mite"},
    {"id": "yellow-citrus-thrips", "name": "Yellow citrus thrips"},
    {"id": "citrus-thrips", "name": "Citrus thrips"},
    {"id": "fruit-sucking-moth", "name": "Fruit sucking moth"},
    {"id": "lemon-butterfly", "name": "Lemon butterfly"},
    {"id": "bark-eating-caterpillar", "name": "Bark eating caterpillar"},
    {"id": "citrus-trunk-borer", "name": "Citrus trunk borer"},
    {"id": "fruit-fly", "name": "Fruit fly"},
]

DEFAULT_MODEL = {
    "version": "untrained-v0",
    "framework": "pytorch/torchvision",
    "status": "untrained",
    "architecture": "mobilenet_v3_small",
    "classes": DEFAULT_CLASSES,
    "checkpoint_path": None,
    "torchscript_path": None,
    "labels_path": None,
    "image_size": 224,
    "confidence_threshold": 0.55,
    "metrics": {"note": "No trained checkpoint registered yet. Upload verified images and train from admin panel."},
    "updated_at": datetime.utcnow().isoformat(),
}

def ensure_store():
    Path(MODEL_STORE).mkdir(parents=True, exist_ok=True)
    Path(MODEL_STORE, "versions").mkdir(parents=True, exist_ok=True)
    Path(MODEL_STORE, "jobs").mkdir(parents=True, exist_ok=True)


def active_model() -> dict:
    ensure_store()
    if os.path.exists(ACTIVE_MODEL_FILE):
        with open(ACTIVE_MODEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    with open(ACTIVE_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_MODEL, f, indent=2)
    return DEFAULT_MODEL


def register_model(version: str, metrics: dict, classes: list[dict], checkpoint_path: str | None = None, torchscript_path: str | None = None, labels_path: str | None = None, architecture: str = "mobilenet_v3_small", image_size: int = 224, status: str = "trained", activate: bool = False) -> dict:
    """Register a model version. The version history always grows; the ACTIVE
    (production) pointer is only moved when activate=True - deployment is an
    explicit governance action (admin deploy/rollback), never a side effect of
    training."""
    payload = {
        "version": version,
        "framework": "pytorch/torchvision",
        "status": status,
        "architecture": architecture,
        "classes": classes,
        "checkpoint_path": checkpoint_path,
        "torchscript_path": torchscript_path,
        "labels_path": labels_path,
        "image_size": image_size,
        "confidence_threshold": float(os.getenv("PEST_CONFIDENCE_THRESHOLD", "0.55")),
        "metrics": metrics,
        "updated_at": datetime.utcnow().isoformat(),
    }
    ensure_store()
    vdir = Path(MODEL_STORE, "versions", version)
    vdir.mkdir(parents=True, exist_ok=True)
    with open(vdir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    if activate:
        with open(ACTIVE_MODEL_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    return payload


def list_versions() -> list[dict]:
    ensure_store()
    out = []
    active = active_model().get("version")
    for meta in sorted(Path(MODEL_STORE, "versions").glob("*/meta.json")):
        try:
            with open(meta, "r", encoding="utf-8") as f:
                m = json.load(f)
            out.append({
                "version": m.get("version"), "status": m.get("status"),
                "architecture": m.get("architecture"), "updated_at": m.get("updated_at"),
                "is_active": m.get("version") == active,
                "accuracy": (m.get("metrics") or {}).get("accuracy"),
                "macro_f1": (m.get("metrics") or {}).get("macro_f1"),
                "checkpoint_registered": bool(m.get("checkpoint_path")),
            })
        except Exception:
            continue
    return out


def version_meta(version: str) -> dict | None:
    p = Path(MODEL_STORE, "versions", version, "meta.json")
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def activate_version(version: str) -> dict:
    """Explicit deployment: validate the artifact, then move the active pointer."""
    meta = version_meta(version)
    if not meta:
        raise ValueError(f"Unknown model version {version}")
    ckpt = meta.get("checkpoint_path")
    if not ckpt or not os.path.exists(ckpt):
        raise ValueError(f"Checkpoint missing for {version}; refusing to activate")
    meta["status"] = meta.get("status") or "trained"
    meta["activated_at"] = datetime.utcnow().isoformat()
    ensure_store()
    with open(ACTIVE_MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta
