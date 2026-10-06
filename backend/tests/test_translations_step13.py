"""Step 13: optional per-language translations for blogs, calendar, events.
Translations are optional; missing languages fall back to base content."""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import BlogPost, CalendarEvent, PlatformEvent
from app.localize import merge_lang
from app.routers.blogs import blog_payload
from app.routers.events import list_events
from app.routers.pests import citrus_calendar

engine = create_engine(f"sqlite:///{tempfile.mkdtemp(prefix='cs-tr13-')}/t.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def test_merge_lang_fallback_and_override():
    data = {"title": "Base title", "description": "Base desc"}
    tr = {"mr": {"title": "मराठी शीर्षक"}}
    assert merge_lang(dict(data), tr, "mr", ["title", "description"])["title"] == "मराठी शीर्षक"
    assert merge_lang(dict(data), tr, "mr", ["title", "description"])["description"] == "Base desc"
    assert merge_lang(dict(data), tr, "hi", ["title", "description"])["title"] == "Base title"
    assert merge_lang(dict(data), tr, "en", ["title", "description"])["title"] == "Base title"


def test_blog_payload_localized():
    db = Session()
    row = BlogPost(title="Monsoon care", summary="sum", body="body", language="en",
                   translations={"mr": {"title": "पावसाळी काळजी", "summary": "सार", "body": "मजकूर"}})
    db.add(row); db.commit()
    en = blog_payload(row, lang="en")
    mr = blog_payload(row, lang="mr")
    hi = blog_payload(row, lang="hi")
    assert en["title"] == "Monsoon care"
    assert mr["title"] == "पावसाळी काळजी" and mr["body"] == "मजकूर"
    assert hi["title"] == "Monsoon care"   # hindi not entered yet -> fallback


def test_events_and_calendar_localized():
    db = Session()
    db.add(PlatformEvent(title="KVK camp", description="Bring samples", event_date="2026-11-01",
                         translations={"hi": {"title": "KVK शिविर", "description": "नमूने लाएं"}}))
    db.add(CalendarEvent(month=10, title="Psyllid watch", description="Scout flush weekly",
                         translations={"mr": {"title": "सायला निरीक्षण", "description": "साप्ताहिक तपासणी"}}))
    db.commit()
    import types
    user = types.SimpleNamespace(id="u1", role="farmer")
    ev_en = list_events(db=db, _user=user)
    ev_hi = list_events(language="hi", db=db, _user=user)
    assert ev_en[0]["title"] == "KVK camp"
    assert ev_hi[0]["title"] == "KVK शिविर"
    cal_mr = citrus_calendar(language="mr", db=db, _=user)
    cal_en = citrus_calendar(db=db, _=user)
    assert cal_mr[0]["title"] == "सायला निरीक्षण"
    assert cal_en[0]["title"] == "Psyllid watch"
