from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..cache import delete_key, get_json, set_json
from ..db import get_db
from ..models import InsecticideRecommendation, User
from ..schemas import InsecticideIn
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/insecticides", tags=["insecticides"])

DEFAULT_DISCLAIMER = "Use only products currently registered by CIB-RC for citrus and follow label dose, PPE and pre-harvest interval. Verify with local agriculture officer before spraying."

FALLBACK = [
    {"pest_id":"citrus-psyllid","pest_name":"Asian citrus psyllid","options":["Neem/azadirachtin for low infestation","Horticultural oil on tender flush","CIB-RC registered systemic/contact insecticide only as per label"],"note":"Vector of HLB. Prioritize monitoring and expert-guided control."},
    {"pest_id":"citrus-leaf-miner","pest_name":"Citrus leaf miner","options":["Neem products on new flush","Pheromone traps where available","CIB-RC registered spinosad/abamectin-type options only if locally labelled"],"note":"Target new flush; avoid unnecessary sprays."},
]

def payload(r: InsecticideRecommendation):
    return {"id": r.id, "pest_id": r.pest_id, "pest_name": r.pest_name, "options": r.options or [], "note": r.note, "disclaimer": r.disclaimer, "is_active": r.is_active, "created_at": r.created_at, "updated_at": r.updated_at}

@router.get("")
def list_insecticides(db: Session = Depends(get_db), _=Depends(get_current_user)):
    cached = get_json("insecticides:active")
    if cached:
        return cached
    rows = db.query(InsecticideRecommendation).filter(InsecticideRecommendation.is_active == True).order_by(InsecticideRecommendation.pest_name).all()
    result = {"title":"Recommended insecticides (CIB-RC)","disclaimer":DEFAULT_DISCLAIMER,"items":[payload(r) for r in rows]} if rows else {"title":"Recommended insecticides (CIB-RC)","disclaimer":DEFAULT_DISCLAIMER,"items":FALLBACK}
    set_json("insecticides:active", result, ttl=600)
    return result

@router.get("/admin")
def admin_list_insecticides(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(InsecticideRecommendation).order_by(InsecticideRecommendation.created_at.desc()).all()
    return [payload(r) for r in rows]

@router.post("/admin")
def admin_create_insecticide(data: InsecticideIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = InsecticideRecommendation(**data.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    delete_key("insecticides:active")
    return {"status":"created", "item": payload(row)}

@router.get("/admin/{item_id}")
def admin_get_insecticide(item_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(InsecticideRecommendation, item_id)
    if not row: raise HTTPException(status_code=404, detail="Recommendation not found")
    return payload(row)

@router.patch("/admin/{item_id}")
def admin_update_insecticide(item_id: str, data: InsecticideIn, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(InsecticideRecommendation, item_id)
    if not row: raise HTTPException(status_code=404, detail="Recommendation not found")
    for k,v in data.model_dump().items(): setattr(row,k,v)
    db.commit(); db.refresh(row)
    delete_key("insecticides:active")
    return {"status":"updated", "item": payload(row)}

@router.post("/admin/{item_id}/toggle")
def admin_toggle_insecticide(item_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(InsecticideRecommendation, item_id)
    if not row: raise HTTPException(status_code=404, detail="Recommendation not found")
    row.is_active = not row.is_active
    db.commit()
    delete_key("insecticides:active")
    return {"status":"updated", "is_active": row.is_active}
