from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..cache import get_json, set_json
from ..db import get_db
from ..models import CalendarEvent, Pest
from ..schemas import PestOut
from ..security import get_current_user
from ..localize import merge_lang

router = APIRouter(prefix="/pests", tags=["pests"])

@router.get("", response_model=list[PestOut])
def list_pests(db: Session = Depends(get_db), _=Depends(get_current_user)):
    cached = get_json("pests:all")
    if cached:
        return cached
    pests = db.query(Pest).order_by(Pest.common_name).all()
    result = [PestOut.model_validate(p).model_dump() for p in pests]
    set_json("pests:all", result, ttl=900)
    return result

@router.get("/calendar/year")
def citrus_calendar(region: str = "India", language: str = "en", db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.query(CalendarEvent).filter(CalendarEvent.region == region).order_by(CalendarEvent.month).all()
    return [merge_lang({"month": r.month, "title": r.title, "description": r.description, "region": r.region}, r.translations, language, ["title", "description"]) for r in rows]

@router.get("/{pest_id}", response_model=PestOut)
def get_pest(pest_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cached = get_json(f"pest:{pest_id}")
    if cached:
        return cached
    pest = db.get(Pest, pest_id)
    if not pest:
        raise HTTPException(status_code=404, detail="Pest not found")
    result = PestOut.model_validate(pest).model_dump()
    set_json(f"pest:{pest_id}", result, ttl=1800)
    return result
