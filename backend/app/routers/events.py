from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..cache import get_json, set_json
from ..db import get_db
from ..models import PlatformEvent, User
from ..security import get_current_user

router = APIRouter(prefix="/events", tags=["events"])

@router.get("")
def list_events(region: str = "India", db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    cache_key = f"events:{region}"
    cached = get_json(cache_key)
    if cached:
        return cached
    rows = db.query(PlatformEvent).filter(PlatformEvent.published == True).order_by(PlatformEvent.event_date.desc()).limit(100).all()
    result = [{"id": e.id, "title": e.title, "description": e.description, "event_date": e.event_date, "region": e.region, "created_at": e.created_at} for e in rows]
    set_json(cache_key, result, ttl=180)
    return result
