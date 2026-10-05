import hashlib
import io
import os
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
import requests
from PIL import Image
from sqlalchemy.orm import Session
from ..admin_notify import create_admin_notification
from ..cache import get_json, set_json
from ..config import settings
from ..db import get_db
from ..media import image_url_for_path
from ..models import Detection, Pest, TrainingImage, User, UserFeedback
from ..schemas import FeedbackIn
from ..security import get_current_user

router = APIRouter(prefix="/detections", tags=["detections"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def save_upload(image: UploadFile, prefix: str = "detections") -> tuple[str, bytes, str]:
    content = image.file.read()
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only jpg, png or webp images are allowed")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large; max 20MB")
    ext = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    folder = os.path.join(settings.upload_dir, prefix)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{uuid.uuid4()}{ext}")
    with open(path, "wb") as f:
        f.write(content)
    sha = hashlib.sha256(content).hexdigest()
    return path, content, sha


def prepare_ai_image(content: bytes, max_size: int = 1024) -> tuple[bytes, str]:
    """Store original image but send optimized JPEG to AI for faster inference."""
    try:
        img = Image.open(io.BytesIO(content)).convert("RGB")
        img.thumbnail((max_size, max_size))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=82, optimize=True)
        return out.getvalue(), "image/jpeg"
    except Exception:
        return content, "image/jpeg"


def pest_details(pest: Pest | None):
    if not pest:
        return None
    return {
        "id": pest.id,
        "name": pest.common_name,
        "common_name": pest.common_name,
        "scientific_name": pest.scientific_name,
        "symptoms": pest.symptoms,
        "lifecycle": pest.lifecycle,
        "prevention": pest.prevention,
        "cure": pest.cure,
        "organic_control": pest.organic_control,
        "chemical_control": pest.chemical_control,
        "safety_note": pest.safety_note,
        "translations": pest.translations or {},
        "image_url": pest.image_url,
    }


def detection_payload(row: Detection):
    return {
        "id": row.id,
        "detection_id": row.id,
        "user_id": row.user_id,
        "user_name": row.user.name if row.user else None,
        "user_phone": row.user.phone if row.user else None,
        "user_details": {"id": row.user.id, "name": row.user.name, "phone": row.user.phone, "district": row.user.district, "village": row.user.village, "state": row.user.state, "acres_land": row.user.acres_land, "plants": row.user.plants} if row.user else None,
        "image_url": image_url_for_path(row.image_path),
        "pest_id": row.pest_id,
        "predicted_name": row.predicted_name,
        "confidence": row.confidence,
        "stage": row.stage,
        "severity_level": row.ai_response.get("severity_level") if isinstance(row.ai_response, dict) else None,
        "source": row.source,
        "ai_response": row.ai_response,
        "admin_status": row.admin_status,
        "admin_note": row.admin_note,
        "corrected_by_admin": row.corrected_by_admin,
        "reviewed_by": row.reviewed_by,
        "reviewed_by_name": row.reviewed_by and (getattr(row, 'reviewer_name', None) or row.reviewed_by),
        "reviewed_at": row.reviewed_at,
        "created_at": row.created_at,
        "pest_details": pest_details(row.pest),
    }

@router.post("")
def detect_pest(
    image: UploadFile = File(...),
    source: str = Form("gallery"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    path, content, sha = save_upload(image)
    cache_key = f"predict:{sha}"
    ai_result = get_json(cache_key)
    if not ai_result:
        try:
            ai_content, ai_type = prepare_ai_image(content)
            response = requests.post(
                f"{settings.ai_service_url}/predict",
                files={"image": ("ai-input.jpg", ai_content, ai_type)},
                timeout=25,
            )
            response.raise_for_status()
            ai_result = response.json()
            set_json(cache_key, ai_result, ttl=60 * 60 * 24)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"AI service unavailable: {exc}") from exc

    is_pest = bool(ai_result.get("is_citrus_pest", True))
    pest_id = ai_result.get("pest_id") if is_pest else None
    pest = db.get(Pest, pest_id) if pest_id else None
    detection = Detection(
        user_id=user.id,
        image_path=path,
        pest_id=pest_id if pest else None,
        predicted_name=ai_result.get("pest_name", "Unknown pest"),
        confidence=float(ai_result.get("confidence", 0)),
        stage=ai_result.get("stage"),
        source=source,
        ai_response=ai_result,
    )
    db.add(detection)
    create_admin_notification(db, "New farmer scan", f"{user.name} uploaded an image. AI result: {detection.predicted_name}", {"type": "detection", "detection_id": detection.id, "user_id": user.id})
    db.commit()
    db.refresh(detection)

    return {
        "detection_id": detection.id,
        "image_url": image_url_for_path(detection.image_path),
        "prediction": ai_result,
        "pest_details": pest_details(pest),
        "message": "No citrus pest detected. Please upload a clear citrus pest, insect or plant-damage image." if not is_pest else ("Low confidence; please retake a clear image or request expert review." if detection.confidence < 0.65 else "Pest detected successfully."),
    }

@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Detection).filter(Detection.user_id == user.id).order_by(Detection.created_at.desc()).limit(100).all()
    return [detection_payload(r) for r in rows]

@router.get("/{detection_id}")
def get_detection(detection_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Detection).filter(Detection.id == detection_id, Detection.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection_payload(row)

@router.post("/{detection_id}/feedback")
def submit_feedback(detection_id: str, payload: FeedbackIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    detection = db.query(Detection).filter(Detection.id == detection_id, Detection.user_id == user.id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    row = UserFeedback(
        detection_id=detection.id,
        user_id=user.id,
        is_correct=payload.is_correct,
        corrected_pest_id=payload.corrected_pest_id,
        comment=payload.comment,
    )
    db.add(row)
    if payload.is_correct is False:
        detection.admin_status = "farmer_feedback_review"
        create_admin_notification(db, "Farmer marked detection wrong", f"{user.name} marked {detection.predicted_name} as wrong.", {"type": "wrong_detection", "detection_id": detection.id, "user_id": user.id, "corrected_pest_id": payload.corrected_pest_id})
    db.commit()
    return {"status": "feedback_saved", "feedback_id": row.id}

@router.post("/{detection_id}/send-for-training")
def send_farmer_image_for_review(detection_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    detection = db.query(Detection).filter(Detection.id == detection_id, Detection.user_id == user.id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    if not detection.pest_id:
        raise HTTPException(status_code=400, detail="Cannot submit unknown pest without admin label")
    item = TrainingImage(
        image_path=detection.image_path,
        pest_id=detection.pest_id,
        stage=detection.stage,
        verified=False,
        source="farmer",
        detection_id=detection.id,
    )
    db.add(item)
    detection.admin_status = "training_review_requested"
    db.commit()
    return {"status": "submitted_for_admin_review", "training_image_id": item.id}
