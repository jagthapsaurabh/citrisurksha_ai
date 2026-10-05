import json
import time
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
import requests
from sqlalchemy.orm import Session
from ..cache import delete_key, delete_pattern
from ..config import settings
from ..db import get_db
from ..media import image_url_for_path
from ..models import AiKnowledgeItem, BlogComment, BlogLike, BlogPost, CalendarEvent, ChatConversation, ChatMessage, Detection, Pest, PlatformEvent, TrainingImage, TrainingJob, User, UserFeedback
from ..schemas import AdminUserIn, AdminUserUpdate, AiKnowledgeIn, BlogIn, CalendarEventIn, ChatMessageIn, DetectionUpdate, PestIn, PlatformEventIn, ResetPasswordIn, TrainingRequest
from ..security import hash_password
from ..security import require_admin
from .detections import detection_payload, save_upload
from .notifications import create_and_send

router = APIRouter(prefix="/admin", tags=["admin"])


def _index_visual_memory(rows: list[TrainingImage], dataset_version: str = "verified-live") -> None:
    """Fire-and-forget push of expert-verified images into the AI service's
    Qdrant visual memory (DINOv2 embeddings). Failures never block review."""
    if not rows:
        return
    try:
        requests.post(
            f"{settings.ai_service_url}/memory/index-verified",
            json={"records": [{
                "image_id": r.id,
                "image_path": r.image_path,
                "pest_id": r.pest_id,
                "stage": r.stage,
                "source": r.source,
                "verification_status": "verified",
                "dataset_version": dataset_version,
            } for r in rows]},
            timeout=30,
        )
    except Exception:
        pass


@router.post("/ai/reindex-memory")
def reindex_visual_memory(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Bulk (re)build the Qdrant visual memory from all verified images."""
    rows = db.query(TrainingImage).filter(TrainingImage.verified == True).order_by(TrainingImage.created_at).all()
    batch, pushed, missing = [], 0, 0
    for i in range(0, len(rows), 25):
        batch = rows[i:i + 25]
        try:
            r = requests.post(
                f"{settings.ai_service_url}/memory/index-verified",
                json={"records": [{
                    "image_id": x.id, "image_path": x.image_path, "pest_id": x.pest_id,
                    "stage": x.stage, "source": x.source, "verification_status": "verified",
                    "dataset_version": "verified-live",
                } for x in batch]},
                timeout=120,
            )
            r.raise_for_status()
            j = r.json()
            pushed += int(j.get("indexed", 0))
            missing += int(j.get("missing", 0))
        except Exception:
            missing += len(batch)
    return {"status": "ok", "verified_images": len(rows), "indexed": pushed, "skipped": missing}


@router.get("/ai/calibration-export")
def calibration_export(limit: int = 500, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Labelled calibration records (expert-reviewed detections only) with the
    full pipeline evidence snapshot. Feed to scripts/calibrate_decision.py."""
    from ..calibration import build_calibration_records
    rows = (db.query(Detection)
            .filter(Detection.reviewed_by.isnot(None) | (Detection.admin_status.in_(["corrected", "approved_for_training"])))
            .order_by(Detection.reviewed_at.desc())
            .limit(min(2000, max(1, limit)))
            .all())
    records = build_calibration_records(rows)
    return {"records": records, "count": len(records)}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return {
        "users": db.query(User).count(),
        "farmers_with_fcm_token": db.query(User).filter(User.role == "farmer", User.fcm_token != None).count(),
        "pests": db.query(Pest).count(),
        "detections": db.query(Detection).count(),
        "unreviewed_detections": db.query(Detection).filter(Detection.admin_status == "unreviewed").count(),
        "training_images_total": db.query(TrainingImage).count(),
        "training_images_verified": db.query(TrainingImage).filter(TrainingImage.verified == True).count(),
        "training_jobs": db.query(TrainingJob).count(),
        "user_feedback": db.query(UserFeedback).count(),
        "ai_knowledge_items": db.query(AiKnowledgeItem).count(),
    }

def save_asset(file: UploadFile, prefix: str = "admin-assets") -> str:
    import os, uuid
    folder = os.path.join(settings.upload_dir, prefix)
    os.makedirs(folder, exist_ok=True)
    ext = os.path.splitext(file.filename or "asset.bin")[1]
    path = os.path.join(folder, f"{uuid.uuid4()}{ext}")
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path

@router.get("/users")
def list_users(role: str | None = None, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    q = db.query(User).order_by(User.created_at.desc())
    if role:
        q = q.filter(User.role == role)
    else:
        q = q.filter(User.role != "farmer")
    rows = q.limit(500).all()
    return [{"id": u.id, "name": u.name, "phone": u.phone, "email": u.email, "role": u.role, "district": u.district, "village": u.village, "state": u.state, "acres_land": u.acres_land, "plants": u.plants, "profile_completed": u.profile_completed, "created_at": u.created_at} for u in rows]

@router.get("/farmers")
def list_farmers(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return list_users(role="farmer", db=db, _admin=_admin)

@router.post("/users")
def create_platform_user(payload: AdminUserIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(status_code=409, detail="Phone already registered")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if payload.role not in {"admin", "agronomist", "data_labeler", "support", "farmer"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = User(name=payload.name, phone=payload.phone, email=payload.email, district=payload.district, role=payload.role, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    return {"status": "created", "user_id": user.id}

@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "phone": user.phone, "email": user.email, "role": user.role, "district": user.district, "village": user.village, "state": user.state, "acres_land": user.acres_land, "plants": user.plants, "is_active": user.is_active, "profile_completed": user.profile_completed, "created_at": user.created_at}

@router.patch("/users/{user_id}")
def update_user(user_id: str, payload: AdminUserUpdate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = payload.model_dump(exclude_unset=True)
    if "phone" in data and data["phone"] != user.phone and db.query(User).filter(User.phone == data["phone"]).first():
        raise HTTPException(status_code=409, detail="Phone already registered")
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    return {"status": "updated", "user_id": user.id}

@router.post("/users/{user_id}/toggle")
def toggle_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"status": "updated", "is_active": user.is_active}

@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: str, payload: ResetPasswordIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"status": "password_reset", "user_id": user.id}

@router.post("/assets")
def upload_asset(file: UploadFile = File(...), db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    path = save_asset(file)
    return {"status": "uploaded", "url": image_url_for_path(path), "filename": file.filename}

@router.post("/pests")
def upsert_pest(payload: PestIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    pest = db.get(Pest, payload.id)
    data = payload.model_dump()
    if pest:
        for key, value in data.items():
            setattr(pest, key, value)
    else:
        pest = Pest(**data)
        db.add(pest)
    db.commit()
    delete_key("pests:all")
    delete_key(f"pest:{payload.id}")
    return {"status": "saved", "pest_id": payload.id}

@router.post("/pests/{pest_id}/toggle")
def toggle_pest(pest_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    pest = db.get(Pest, pest_id)
    if not pest:
        raise HTTPException(status_code=404, detail="Pest not found")
    pest.is_active = not pest.is_active
    db.commit()
    delete_key("pests:all")
    delete_key(f"pest:{pest_id}")
    return {"status": "updated", "is_active": pest.is_active}

@router.get("/detections/review")
def detections_to_review(status: str | None = None, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    q = db.query(Detection).order_by(Detection.created_at.desc())
    if status:
        q = q.filter(Detection.admin_status == status)
    rows = q.limit(300).all()
    result = []
    reviewer_ids = {r.reviewed_by for r in rows if r.reviewed_by}
    reviewers = {u.id: u.name for u in db.query(User).filter(User.id.in_(reviewer_ids)).all()} if reviewer_ids else {}
    for r in rows:
        item = detection_payload(r)
        item["reviewed_by_name"] = reviewers.get(r.reviewed_by)
        result.append(item)
    return result

@router.get("/detections/{detection_id}")
def admin_get_detection(detection_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(Detection, detection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection_payload(row)

@router.patch("/detections/{detection_id}")
def admin_update_detection(detection_id: str, payload: DetectionUpdate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(Detection, detection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Detection not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("pest_id"):
        pest = db.get(Pest, data["pest_id"])
        if not pest:
            raise HTTPException(status_code=400, detail="Unknown pest_id")
        row.pest_id = pest.id
        if not data.get("predicted_name"):
            row.predicted_name = pest.common_name
    for field in ["predicted_name", "confidence", "stage", "admin_status", "admin_note"]:
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    row.corrected_by_admin = True
    row.reviewed_by = _admin.id
    row.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return {"status": "updated", "detection": detection_payload(row)}

@router.post("/detections/{detection_id}/approve-training")
def approve_detection_for_training(
    detection_id: str,
    pest_id: str = Form(...),
    stage: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    detection = db.get(Detection, detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    if not db.get(Pest, pest_id):
        raise HTTPException(status_code=400, detail="Unknown pest_id")
    detection.admin_status = "approved_for_training"
    detection.pest_id = pest_id
    detection.reviewed_by = _admin.id
    detection.reviewed_at = datetime.utcnow()
    item = TrainingImage(image_path=detection.image_path, pest_id=pest_id, stage=stage or detection.stage, verified=True, source="farmer", detection_id=detection.id)
    db.add(item)
    db.commit()
    _index_visual_memory([item])
    return {"status": "approved", "training_image_id": item.id}

@router.post("/training-images")
def upload_training_image(
    image: UploadFile = File(...),
    pest_id: str = Form(...),
    stage: str | None = Form(None),
    verified: bool = Form(True),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if not db.get(Pest, pest_id):
        db.add(Pest(id=pest_id, common_name=pest_id.replace('-', ' ').title(), category='custom', symptoms='Custom pest added from training upload. Please complete pest details.', prevention='', cure=''))
        db.flush()
    path, _, _ = save_upload(image, prefix="training")
    row = TrainingImage(image_path=path, pest_id=pest_id, stage=stage, verified=verified, source="admin")
    db.add(row)
    db.commit()
    return {"status": "uploaded", "training_image_id": row.id, "image_url": image_url_for_path(row.image_path)}

@router.get("/training-images/pending")
def pending_training_images(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(TrainingImage).filter(TrainingImage.verified == False).order_by(TrainingImage.created_at.desc()).limit(300).all()
    return [
        {"id": r.id, "image_url": image_url_for_path(r.image_path), "pest_id": r.pest_id, "stage": r.stage, "source": r.source, "created_at": r.created_at}
        for r in rows
    ]

@router.post("/training-images/{training_image_id}/verify")
def verify_training_image(
    training_image_id: str,
    pest_id: str | None = Form(None),
    stage: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    row = db.get(TrainingImage, training_image_id)
    if not row:
        raise HTTPException(status_code=404, detail="Training image not found")
    if pest_id:
        if not db.get(Pest, pest_id):
            raise HTTPException(status_code=400, detail="Unknown pest_id")
        row.pest_id = pest_id
    if stage:
        row.stage = stage
    row.verified = True
    db.commit()
    _index_visual_memory([row])
    return {"status": "verified", "training_image_id": row.id, "pest_id": row.pest_id, "stage": row.stage}

@router.get("/ai/class-coverage")
def ai_class_coverage(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    pests = db.query(Pest).order_by(Pest.common_name).all()
    verified = db.query(TrainingImage).filter(TrainingImage.verified == True).all()
    counts = {}
    for row in verified:
        counts[row.pest_id] = counts.get(row.pest_id, 0) + 1
    rows = [{"pest_id": p.id, "name": p.common_name, "verified_images": counts.get(p.id, 0), "ready": counts.get(p.id, 0) > 0} for p in pests]
    rows.insert(0, {"pest_id": "no-citrus-pest", "name": "No citrus pest / negative images", "verified_images": counts.get("no-citrus-pest", 0), "ready": counts.get("no-citrus-pest", 0) > 0})
    missing = [r["pest_id"] for r in rows if not r["ready"]]
    return {"classes": rows, "total_classes": len(rows), "ready_classes": len(rows) - len(missing), "missing_classes": missing, "all_20_pests_ready": all(r["ready"] for r in rows if r["pest_id"] != "no-citrus-pest")}

@router.get("/ai/free-models")
def free_base_models(_admin: User = Depends(require_admin)):
    try:
        response = requests.get(f"{settings.ai_service_url}/models/free-base-models", timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {
            "models": [
                {"id": "mobilenet_v3_small", "name": "MobileNetV3 Small", "license": "TorchVision BSD-style", "best_for": "8-core CPU VPS"},
                {"id": "mobilenet_v3_large", "name": "MobileNetV3 Large", "license": "TorchVision BSD-style", "best_for": "better accuracy"},
                {"id": "resnet18", "name": "ResNet-18", "license": "TorchVision BSD-style", "best_for": "stable baseline"},
            ]
        }

@router.post("/ai/feed-data")
def feed_ai_data(payload: AiKnowledgeIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    content = payload.content
    metadata = payload.metadata or {}
    if payload.url and not content:
        try:
            r = requests.get(payload.url, timeout=20, headers={"User-Agent": "CitriSurkshaBot/0.1"})
            r.raise_for_status()
            # Minimal browser ingest: strip tags enough for model context. Use a real crawler pipeline in production.
            content = " ".join(__import__("re").sub("<[^<]+?>", " ", r.text).split())[:12000]
            metadata["fetched_url"] = payload.url
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not fetch URL: {exc}") from exc
    if not content:
        raise HTTPException(status_code=400, detail="Provide content or a fetchable URL")
    row = AiKnowledgeItem(
        source_type=payload.source_type,
        title=payload.title,
        content=content,
        url=payload.url,
        pest_id=payload.pest_id,
        metadata_json=metadata,
        created_by=admin.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    try:
        requests.post(f"{settings.ai_service_url}/knowledge/items", json={"source_type": row.source_type, "title": row.title, "content": row.content, "url": row.url, "pest_id": row.pest_id, "metadata": row.metadata_json}, timeout=15)
    except Exception:
        pass
    return {"status": "stored", "id": row.id}

@router.get("/ai/feed-data")
def list_ai_feed_data(source_type: str | None = None, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    q = db.query(AiKnowledgeItem).order_by(AiKnowledgeItem.created_at.desc())
    if source_type:
        q = q.filter(AiKnowledgeItem.source_type == source_type)
    rows = q.limit(500).all()
    return [{"id": r.id, "source_type": r.source_type, "title": r.title, "content": r.content[:500], "url": r.url, "pest_id": r.pest_id, "created_at": r.created_at} for r in rows]

@router.get("/ai/unknown-clusters")
def unknown_clusters_proxy(_admin: User = Depends(require_admin)):
    try:
        r = requests.get(f"{settings.ai_service_url}/active-learning/unknown-clusters", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"clusters": [], "total_unknowns": 0, "error": str(exc)}


@router.post("/ai/tune-priority")
def tune_priority_proxy(payload: dict, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Feed the calibration export into priority-weight tuning."""
    from ..calibration import build_calibration_records
    rows = (db.query(Detection)
            .filter(Detection.reviewed_by.isnot(None))
            .order_by(Detection.reviewed_at.desc()).limit(2000).all())
    records = build_calibration_records(rows)
    try:
        r = requests.post(f"{settings.ai_service_url}/active-learning/tune",
                          json={"records": records}, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tuning failed: {exc}") from exc


def _drive_scripts():
    import importlib.util
    root = Path(__file__).resolve().parents[3]
    fetch = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location("fetch_open_drive", root / "scripts" / "fetch_open_drive.py"))
    import sys
    sys.modules.setdefault("fetch_open_drive", fetch)
    fetch.__spec__.loader.exec_module(fetch)
    ingest = importlib.util.module_from_spec(
        importlib.util.spec_from_file_location("ingest_tool", root / "scripts" / "ingest_labelled_images.py"))
    sys.modules.setdefault("ingest_tool", ingest)
    ingest.__spec__.loader.exec_module(ingest)
    return fetch, ingest


def _training_images_dir() -> Path:
    return Path(settings.upload_dir).parent / "training_images"


@router.get("/ai/drive/status")
def drive_status(_admin: User = Depends(require_admin)):
    """Live view of the open/labelled image drive per pest class."""
    base = _training_images_dir()
    prov = base / "provenance.jsonl"
    prov_rows = 0
    sources: dict = {}
    if prov.exists():
        for line in prov.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                prov_rows += 1
                key = f"{r.get('source_dataset', 'local')} ({r.get('license', '-')})"
                sources[key] = sources.get(key, 0) + 1
            except Exception:
                continue
    classes = []
    for d in sorted(base.iterdir()):
        if d.is_dir():
            n = len([f for f in d.glob("*") if "ingested" in f.name])
            if n or (d / ".keep").exists():
                classes.append({"pest_id": d.name, "images": n})
    return {"classes": classes, "provenance_records": prov_rows, "sources": sources}


@router.post("/ai/drive/fetch")
def drive_fetch(payload: dict | None = None, _admin: User = Depends(require_admin)):
    """Fetch open-licensed transfer images (MIT / Apache-2.0) and ingest them
    with dedupe + provenance. Small per_class keeps the call inside timeouts."""
    fetch, ingest = _drive_scripts()
    per = int((payload or {}).get("per_class", 4))
    src = (payload or {}).get("source", "all")
    src_dir = _training_images_dir() / ".drive_src"
    src_dir.mkdir(parents=True, exist_ok=True)
    prov: list = []
    out = {"leafminer": None, "ip102": None}
    if src in ("leafminer", "all"):
        out["leafminer"] = fetch.fetch_leafminer(src_dir, per, prov)
    if src in ("ip102", "all"):
        out["ip102"] = fetch.fetch_ip102(src_dir, per, prov, offset=int((payload or {}).get("offset", 0)),
                                         max_pages=int((payload or {}).get("max_pages", 12)))
    rep = ingest.ingest(src_dir, _training_images_dir(), _training_images_dir() / "provenance.jsonl")
    return {"fetched": out, "ingested": rep.get("copied"), "classes": rep.get("classes")}


@router.post("/ai/drive/train-cnn")
def drive_train_cnn(payload: dict | None = None, _admin: User = Depends(require_admin)):
    """Experimental CNN training on the drive images (transfer classes)."""
    base = _training_images_dir()
    records = []
    classes = []
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        files = [f for f in sorted(d.glob("*")) if "ingested" in f.name]
        if not files:
            continue
        classes.append({"id": d.name, "name": d.name.replace("-", " ").title()})
        for f in files:
            records.append({"image_id": f.stem, "image_path": str(f), "pest_id": d.name})
    body = {
        "dataset_version": (payload or {}).get("dataset_version") or f"drive-{time.strftime('%Y%m%d-%H%M')}",
        "base_model": (payload or {}).get("base_model", "resnet18"),
        "epochs": int((payload or {}).get("epochs", 8)),
        "batch_size": int((payload or {}).get("batch_size", 8)),
        "image_size": 128,
        "classes": classes,
        "training_records": records,
        "experimental": True,
    }
    try:
        r = requests.post(f"{settings.ai_service_url}/train/jobs", json=body, timeout=900)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"CNN training failed: {exc}") from exc


@router.post("/ai/drive/train-yolo")
def drive_train_yolo(payload: dict | None = None, _admin: User = Depends(require_admin)):
    """Experimental bootstrap YOLO training on the drive images."""
    base = _training_images_dir()
    records = []
    for d in sorted(base.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        for f in sorted(d.glob("*")):
            if "ingested" in f.name:
                records.append({"image_id": f.stem, "image_path": str(f), "pest_id": d.name})
    body = {"dataset_version": (payload or {}).get("dataset_version") or f"drive-yolo-{time.strftime('%Y%m%d-%H%M')}",
            "records": records, "epochs": int((payload or {}).get("epochs", 2)),
            "imgsz": int((payload or {}).get("imgsz", 192)), "batch": 1}
    try:
        r = requests.post(f"{settings.ai_service_url}/train/yolo", json=body, timeout=1800)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"YOLO training failed: {exc}") from exc


@router.get("/ai/review-queue")
def review_queue(limit: int = 50, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Active-learning priority queue: unreviewed detections ordered by the
    pipeline's review_priority (low confidence, unknown, model disagreement)."""
    rows = (db.query(Detection)
            .filter(Detection.admin_status.in_(["unreviewed", "pending"]))
            .order_by(Detection.created_at.desc()).limit(500).all())
    out = []
    for r in rows:
        ai = r.ai_response or {}
        out.append({
            "id": r.id, "image_url": image_url_for_path(r.image_path),
            "predicted_name": r.predicted_name, "confidence": r.confidence,
            "decision": ai.get("decision"), "review_priority": ai.get("review_priority") or 0.0,
            "user_name": getattr(r.user, "name", None), "created_at": r.created_at,
        })
    out.sort(key=lambda x: x["review_priority"], reverse=True)
    return {"queue": out[: max(1, min(200, limit))]}


@router.get("/ai/datasets")
def list_dataset_versions(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from ..models import DatasetVersion
    rows = db.query(DatasetVersion).order_by(DatasetVersion.created_at.desc()).limit(100).all()
    return {"datasets": [{
        "version": r.version, "annotation_version": r.annotation_version,
        "image_count": r.image_count, "class_distribution": r.class_distribution,
        "train_count": r.train_count, "val_count": r.val_count, "test_count": r.test_count,
        "dups_removed": r.dups_removed, "created_at": r.created_at,
        "frozen_inherited": bool(r.frozen_test_ids),
    } for r in rows]}


@router.post("/ai/datasets")
def create_dataset_version(payload: dict, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Build an immutable dataset version (frozen test set, dedupe) in the AI
    service and store its governance metadata here."""
    from ..models import DatasetVersion
    version = (payload or {}).get("version")
    if not version:
        raise HTTPException(status_code=400, detail="version required")
    if db.query(DatasetVersion).filter(DatasetVersion.version == version).first():
        raise HTTPException(status_code=400, detail="Dataset version already exists (immutable)")
    prev = db.query(DatasetVersion).order_by(DatasetVersion.created_at.desc()).first()
    verified = db.query(TrainingImage).filter(TrainingImage.verified == True).all()
    try:
        r = requests.post(f"{settings.ai_service_url}/datasets/build", json={
            "version": version,
            "previous_frozen_test_ids": prev.frozen_test_ids if prev else None,
            "annotation_version": payload.get("annotation_version", "v1"),
            "records": [{"image_id": x.id, "image_path": x.image_path, "pest_id": x.pest_id,
                         "stage": x.stage, "source": x.source} for x in verified],
        }, timeout=300)
        r.raise_for_status()
        m = r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dataset build failed: {exc}") from exc
    row = DatasetVersion(
        version=version, annotation_version=m.get("annotation_version", "v1"),
        image_count=m.get("image_count", 0), class_distribution=m.get("class_distribution", {}),
        train_count=m.get("train_count", 0), val_count=m.get("val_count", 0),
        test_count=m.get("test_count", 0), frozen_test_ids=m.get("frozen_test_ids", []),
        dups_removed=m.get("dups_removed", 0), created_by=_admin.id,
        notes=payload.get("notes"))
    db.add(row)
    db.commit()
    return {"status": "created", "dataset": m}


@router.post("/ai/train")
def start_training(payload: TrainingRequest, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from ..models import DatasetVersion, ModelVersion
    pests = db.query(Pest).order_by(Pest.common_name).all()
    verified_images = db.query(TrainingImage).filter(TrainingImage.verified == True).order_by(TrainingImage.created_at.desc()).limit(5000).all()
    knowledge = db.query(AiKnowledgeItem).order_by(AiKnowledgeItem.created_at.desc()).limit(1000).all()

    # Leakage guard: when a dataset version exists, train ONLY on its train+val
    # splits; the frozen test set never reaches training.
    manifest = None
    if payload.dataset_version:
        try:
            mr = requests.get(f"{settings.ai_service_url}/datasets/{payload.dataset_version}", timeout=30)
            if mr.ok:
                manifest = mr.json()
        except Exception:
            manifest = None
    if manifest:
        allowed = {i for i, s in (manifest.get("splits") or {}).items() if s in ("train", "val")}
        verified_images = [r for r in verified_images if r.id in allowed]

    payload.classes = payload.classes or [{"id": p.id, "name": p.common_name, "scientific_name": p.scientific_name, "symptoms": p.symptoms, "prevention": p.prevention, "cure": p.cure} for p in pests]
    payload.training_records = payload.training_records or [{"id": r.id, "pest_id": r.pest_id, "stage": r.stage, "source": r.source, "image_path": r.image_path, "image_url": image_url_for_path(r.image_path), "created_at": str(r.created_at)} for r in verified_images]
    payload.knowledge_records = payload.knowledge_records or [{"id": r.id, "source_type": r.source_type, "title": r.title, "content": r.content, "url": r.url, "pest_id": r.pest_id, "metadata": r.metadata_json} for r in knowledge]

    model_row = ModelVersion(
        version=f"pending-{payload.dataset_version or 'adhoc'}-{_admin.id[:4]}",
        architecture=payload.base_model, dataset_version=payload.dataset_version,
        image_size=224, status="training", created_by=_admin.id,
        training_config={"epochs": payload.epochs, "batch_size": payload.batch_size,
                         "base_model": payload.base_model,
                         "min_accuracy_gate": payload.min_accuracy_gate,
                         "dataset_manifest": bool(manifest)})
    db.add(model_row)

    job = TrainingJob(dataset_version=payload.dataset_version, status="queued", metrics={"base_model": payload.base_model, "records_sent": len(payload.training_records), "knowledge_sent": len(payload.knowledge_records)})
    db.add(job)
    db.commit()
    try:
        response = requests.post(f"{settings.ai_service_url}/train/jobs", json=payload.model_dump(), timeout=240)
        response.raise_for_status()
        ai_job = response.json()
        job.ai_job_id = ai_job.get("job_id")
        job.status = ai_job.get("status", "queued")
        job.metrics = ai_job.get("metrics", job.metrics)
        v = ai_job.get("model_version")
        if v:
            model_row.version = v
            model_row.metrics = ai_job.get("metrics", {}) or {}
            model_row.environment = ai_job.get("environment", {}) or {}
            model_row.checkpoint_path = (ai_job.get("artifacts") or {}).get("checkpoint_path")
            model_row.torchscript_path = (ai_job.get("artifacts") or {}).get("torchscript_path")
            model_row.labels = payload.classes or []
            model_row.status = "testing"
        else:
            model_row.status = "rejected"
            model_row.metrics = ai_job.get("metrics", {}) or {}
        db.commit()
    except Exception as exc:
        job.status = "failed_to_queue"
        job.metrics = {"error": str(exc)}
        db.commit()
        raise HTTPException(status_code=502, detail=f"Could not queue AI training: {exc}") from exc
    return {"status": job.status, "backend_job_id": job.id, "ai_job_id": job.ai_job_id, "metrics": job.metrics}

@router.post("/ai/train-yolo")
def start_yolo_training(payload: dict, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Bootstrap the YOLO11 detector stage from verified classification images."""
    from ..models import ModelVersion
    dataset_version = (payload or {}).get("dataset_version") or "yolo-bootstrap"
    verified = db.query(TrainingImage).filter(TrainingImage.verified == True).all()
    splits = None
    if dataset_version:
        try:
            mr = requests.get(f"{settings.ai_service_url}/datasets/{dataset_version}", timeout=30)
            if mr.ok:
                splits = (mr.json() or {}).get("splits")
        except Exception:
            splits = None
    try:
        r = requests.post(f"{settings.ai_service_url}/train/yolo", json={
            "dataset_version": dataset_version,
            "epochs": int((payload or {}).get("epochs", 10)),
            "imgsz": int((payload or {}).get("imgsz", 640)),
            "splits": splits,
            "records": [{"image_id": x.id, "image_path": x.image_path, "pest_id": x.pest_id} for x in verified],
        }, timeout=3600)
        r.raise_for_status()
        result = r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"YOLO training failed to start: {exc}") from exc
    if result.get("version"):
        db.add(ModelVersion(
            version=result["version"], architecture=result.get("architecture", "yolo11s"),
            dataset_version=dataset_version, checkpoint_path=result.get("checkpoint_path"),
            image_size=int((payload or {}).get("imgsz", 640)), status="testing",
            created_by=_admin.id, metrics=result.get("metrics", {}),
            training_config={"type": "yolo_bootstrap", "epochs": (payload or {}).get("epochs", 10),
                             "bootstrap_labels": True}))
        db.commit()
    return result


@router.get("/ai/jobs")
def list_training_jobs(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).limit(100).all()
    return [{"id": r.id, "dataset_version": r.dataset_version, "status": r.status, "ai_job_id": r.ai_job_id, "metrics": r.metrics, "created_at": r.created_at} for r in rows]

@router.get("/blogs")
def admin_list_blogs(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(BlogPost).order_by(BlogPost.created_at.desc()).limit(300).all()
    return [{"id": b.id, "title": b.title, "summary": b.summary, "body": b.body, "language": b.language, "published": b.published, "image_url": b.image_url, "doc_url": b.doc_url, "content_type": b.content_type, "author_name": b.author_name, "views_count": b.views_count or 0, "likes_count": db.query(BlogLike).filter(BlogLike.blog_id == b.id).count(), "comments_count": db.query(BlogComment).filter(BlogComment.blog_id == b.id).count(), "created_at": b.created_at} for b in rows]

@router.post("/blogs")
def create_blog(payload: BlogIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = BlogPost(**payload.model_dump())
    db.add(row)
    db.commit()
    delete_pattern("blogs:*")
    return {"status": "published" if row.published else "draft", "blog_id": row.id}

@router.patch("/blogs/{blog_id}")
def update_blog(blog_id: str, payload: BlogIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(BlogPost, blog_id)
    if not row:
        raise HTTPException(status_code=404, detail="Blog not found")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    delete_pattern("blogs:*")
    return {"status": "updated", "blog_id": row.id}

@router.delete("/blogs/{blog_id}")
def delete_blog(blog_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(BlogPost, blog_id)
    if not row:
        raise HTTPException(status_code=404, detail="Blog not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}

@router.get("/calendar")
def admin_list_calendar(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(CalendarEvent).order_by(CalendarEvent.month).all()
    return [{"id": r.id, "month": r.month, "title": r.title, "description": r.description, "region": r.region} for r in rows]

@router.get("/calendar/{event_id}")
def admin_get_calendar(event_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(CalendarEvent, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar operation not found")
    return {"id": row.id, "month": row.month, "title": row.title, "description": row.description, "region": row.region}

@router.post("/calendar")
def upsert_calendar_event(payload: CalendarEventIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.query(CalendarEvent).filter(CalendarEvent.month == payload.month, CalendarEvent.region == payload.region).first()
    if row:
        row.title = payload.title
        row.description = payload.description
    else:
        row = CalendarEvent(**payload.model_dump())
        db.add(row)
    db.commit()
    return {"status": "saved", "id": row.id, "month": row.month, "region": row.region}

@router.patch("/calendar/{event_id}")
def update_calendar_event(event_id: str, payload: CalendarEventIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(CalendarEvent, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar operation not found")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    return {"status": "updated", "id": row.id}

@router.delete("/calendar/{event_id}")
def delete_calendar_event(event_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(CalendarEvent, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Calendar operation not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}

@router.get("/events")
def list_events(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(PlatformEvent).order_by(PlatformEvent.created_at.desc()).limit(300).all()
    return [{"id": e.id, "title": e.title, "description": e.description, "event_date": e.event_date, "region": e.region, "send_notification": e.send_notification, "published": e.published, "created_at": e.created_at} for e in rows]

@router.post("/events")
def create_event(payload: PlatformEventIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = PlatformEvent(**payload.model_dump())
    db.add(row)
    db.flush()
    pushed = 0
    if row.send_notification and row.published:
        farmers = db.query(User).filter(User.role == "farmer").all()
        for farmer in farmers:
            create_and_send(db, farmer, f"New event: {row.title}", row.description, {"type": "event", "event_id": row.id})
            pushed += 1
    db.commit()
    return {"status": "created", "event_id": row.id, "notification_queued": row.send_notification, "farmers_notified": pushed}

@router.patch("/events/{event_id}")
def update_event(event_id: str, payload: PlatformEventIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(PlatformEvent, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    return {"status": "updated", "event_id": row.id}

@router.delete("/events/{event_id}")
def delete_event(event_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(PlatformEvent, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}

@router.get("/chats")
def list_chats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    convs = db.query(ChatConversation).order_by(ChatConversation.created_at.desc()).limit(300).all()
    result = []
    for c in convs:
        farmer = db.get(User, c.farmer_id)
        last = db.query(ChatMessage).filter(ChatMessage.conversation_id == c.id).order_by(ChatMessage.created_at.desc()).first()
        result.append({"id": c.id, "farmer_id": c.farmer_id, "farmer_name": farmer.name if farmer else c.farmer_id, "assigned_to": c.assigned_to, "status": c.status, "subject": c.subject, "last_message": last.message if last else "", "created_at": c.created_at})
    return result

@router.get("/chats/{conversation_id}/messages")
def chat_messages(conversation_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at).all()
    return [{"id": m.id, "sender_id": m.sender_id, "sender_role": m.sender_role, "message": m.message, "created_at": m.created_at} for m in rows]

@router.post("/chats/{conversation_id}/messages")
async def admin_send_chat(conversation_id: str, payload: ChatMessageIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    conv = db.get(ChatConversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.assigned_to = admin.id
    row = ChatMessage(conversation_id=conversation_id, sender_id=admin.id, sender_role=admin.role, message=payload.message)
    db.add(row)
    db.commit(); db.refresh(row)
    from .chat import broadcast_message
    await broadcast_message(conversation_id, row)
    return {"status": "sent", "message_id": row.id}

@router.post("/chats/{conversation_id}/attachments")
async def admin_send_chat_attachment(conversation_id: str, message: str = Form(""), file: UploadFile = File(...), db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    conv = db.get(ChatConversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    from .chat import save_chat_file, broadcast_message
    path, name, ctype = save_chat_file(file)
    conv.assigned_to = admin.id
    row = ChatMessage(conversation_id=conversation_id, sender_id=admin.id, sender_role=admin.role, message=message or name, attachment_url=image_url_for_path(path), attachment_name=name, attachment_type=ctype)
    db.add(row)
    db.commit(); db.refresh(row)
    await broadcast_message(conversation_id, row)
    return {"status": "sent", "message_id": row.id, "attachment_url": row.attachment_url}

@router.get("/system/database")
def system_database(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from sqlalchemy import inspect
    from ..db import engine
    from ..config import settings
    inspector = inspect(engine)
    url = settings.database_url
    masked = url
    if '@' in masked and '://' in masked:
        prefix, rest = masked.split('://', 1)
        if '@' in rest:
            creds, host = rest.split('@', 1)
            user = creds.split(':', 1)[0]
            masked = f"{prefix}://{user}:***@{host}"
    return {"dialect": engine.dialect.name, "database_url": masked, "tables": inspector.get_table_names(), "table_count": len(inspector.get_table_names())}

@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == _admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    db.delete(user)
    db.commit()
    return {"status": "deleted", "user_id": user_id}

@router.delete("/pests/{pest_id}")
def delete_pest(pest_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    pest = db.get(Pest, pest_id)
    if not pest:
        raise HTTPException(status_code=404, detail="Pest not found")
    db.delete(pest)
    db.commit()
    delete_key("pests:all")
    delete_key(f"pest:{pest_id}")
    return {"status": "deleted", "pest_id": pest_id}

@router.get("/ai/models")
def list_ai_models(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Governed model registry (DB) + live active pointer from the AI service."""
    from ..models import ModelVersion
    active = {}
    try:
        r = requests.get(f"{settings.ai_service_url}/models/active", timeout=10)
        if r.ok:
            active = r.json()
    except Exception:
        active = {}
    rows = db.query(ModelVersion).order_by(ModelVersion.updated_at.desc()).limit(100).all()
    models = [{
        "id": r.id, "version": r.version, "status": r.status, "architecture": r.architecture,
        "dataset_version": r.dataset_version, "image_size": r.image_size,
        "training_config": r.training_config, "environment": r.environment,
        "metrics": r.metrics, "was_production": r.was_production,
        "has_checkpoint": bool(r.checkpoint_path), "has_torchscript": bool(r.torchscript_path),
        "progress_percent": 100 if r.checkpoint_path else 0,
        "is_active": r.version == active.get("version"),
        "created_at": r.created_at, "updated_at": r.updated_at,
    } for r in rows]
    return {"active": active, "models": models}


@router.post("/ai/models/{model_id}/status")
def set_ai_model_status(model_id: str, payload: dict, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from ..model_governance import set_model_status
    from ..models import ModelVersion
    row = db.get(ModelVersion, model_id)
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    set_model_status(db, row, (payload or {}).get("status", ""), _admin.id)
    return {"status": row.status, "model_id": row.id}


@router.post("/ai/models/{model_id}/deploy")
def deploy_ai_model(model_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from ..model_governance import deploy_model
    from ..models import ModelVersion
    row = db.get(ModelVersion, model_id)
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    return deploy_model(db, row, _admin.id)


@router.post("/ai/models/{model_id}/evaluate")
def evaluate_ai_model(model_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Frozen-test evaluation; the report is stored on the model row and gates deploy."""
    from ..models import DatasetVersion, ModelVersion, TrainingImage
    row = db.get(ModelVersion, model_id)
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    if not row.dataset_version:
        raise HTTPException(status_code=400, detail="Model has no dataset_version; cannot locate frozen test set")
    ds = db.query(DatasetVersion).filter(DatasetVersion.version == row.dataset_version).first()
    if not ds:
        raise HTTPException(status_code=400, detail="Dataset version row missing")
    verified = db.query(TrainingImage).filter(TrainingImage.verified == True).all()
    try:
        r = requests.post(f"{settings.ai_service_url}/models/evaluate", json={
            "version": row.version, "dataset_version": row.dataset_version,
            "records": [{"image_id": x.id, "image_path": x.image_path, "pest_id": x.pest_id} for x in verified],
        }, timeout=600)
        r.raise_for_status()
        report = r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Evaluation failed: {exc}") from exc
    metrics = dict(row.metrics or {})
    metrics["frozen_eval"] = report
    row.metrics = metrics
    db.commit()
    return {"model_id": row.id, "frozen_eval": report}


@router.post("/ai/models/{model_id}/compare")
def compare_ai_model(model_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Compare candidate vs current production on their frozen evaluations."""
    from ..models import ModelVersion
    row = db.get(ModelVersion, model_id)
    if not row:
        raise HTTPException(status_code=404, detail="Model not found")
    prod = db.query(ModelVersion).filter(ModelVersion.status == "production").first()
    candidate_eval = (row.metrics or {}).get("frozen_eval")
    if not candidate_eval:
        raise HTTPException(status_code=400, detail="Candidate has no frozen_eval; evaluate it first")
    current_eval = (prod.metrics or {}).get("frozen_eval") if prod and prod.id != row.id else None
    try:
        r = requests.post(f"{settings.ai_service_url}/models/compare",
                          json={"current": current_eval, "candidate": candidate_eval}, timeout=60)
        r.raise_for_status()
        comparison = r.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Comparison failed: {exc}") from exc
    metrics = dict(row.metrics or {})
    metrics["comparison"] = comparison
    row.metrics = metrics
    db.commit()
    return {"model_id": row.id, "comparison": comparison}


@router.post("/ai/models/rollback")
def rollback_ai_model(payload: dict | None = None, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    from ..model_governance import rollback_model
    return rollback_model(db, _admin.id, (payload or {}).get("model_id"))
