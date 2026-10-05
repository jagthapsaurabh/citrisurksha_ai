from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Pest, TrainingImage, User
from ..security import get_current_user
from .detections import save_upload

router = APIRouter(prefix="/training", tags=["training"])

@router.post("/farmer-images")
def submit_farmer_training_image(
    image: UploadFile = File(...),
    pest_id: str = Form(...),
    stage: str | None = Form(None),
    note: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Allow farmers to contribute labelled images to improve AI.

    Images submitted from the mobile app are NOT used directly for training. They are
    stored as unverified data and must be reviewed/approved by an admin/agronomist.
    """
    if not db.get(Pest, pest_id):
        raise HTTPException(status_code=400, detail="Please select a valid pest from the pest list")
    path, _, _ = save_upload(image, prefix="farmer-training")
    row = TrainingImage(
        image_path=path,
        pest_id=pest_id,
        stage=stage,
        verified=False,
        source=f"farmer:{user.id}",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "status": "submitted_for_admin_review",
        "training_image_id": row.id,
        "message": "Thank you. Your image will be checked by an expert before it is used to train CitriSurksha AI.",
        "note_received": note,
    }

@router.get("/my-submissions")
def my_training_submissions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(TrainingImage).filter(TrainingImage.source == f"farmer:{user.id}").order_by(TrainingImage.created_at.desc()).limit(100).all()
    return [
        {"id": r.id, "pest_id": r.pest_id, "stage": r.stage, "verified": r.verified, "created_at": r.created_at}
        for r in rows
    ]
