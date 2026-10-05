"""Smoke-test CitriSurksha backend database queries.

Usage from project root or backend folder:
  python scripts/check_backend_queries.py
  TEST_DATABASE_URL=postgresql+psycopg2://postgres:pass@localhost:5432/citrisurksha_test python scripts/check_backend_queries.py

By default this uses a temporary SQLite database so it is safe.
For PostgreSQL, pass TEST_DATABASE_URL. Prefer a test DB because this script creates rows.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
else:
    tmp = Path(tempfile.gettempdir()) / "citrisurksha_query_smoke.db"
    if tmp.exists():
        tmp.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp.as_posix()}"

os.environ.setdefault("API_SECRET_KEY", "test-secret")
os.environ.setdefault("AI_SERVICE_URL", "http://localhost:8100")
os.environ.setdefault("UPLOAD_DIR", str(ROOT / "storage" / "uploads"))

from app.db import Base, engine, SessionLocal  # noqa: E402
from app.main import ensure_lightweight_migrations, seed_data  # noqa: E402
from app.models import (  # noqa: E402
    AiKnowledgeItem,
    BlogComment,
    BlogLike,
    BlogPost,
    CalendarEvent,
    ChatConversation,
    ChatMessage,
    Detection,
    FarmerNotification,
    InsecticideRecommendation,
    Pest,
    PlatformEvent,
    PushNotificationCampaign,
    TrainingImage,
    TrainingJob,
    User,
    UserFeedback,
)
from app.security import hash_password  # noqa: E402


def assert_count(db, model, name: str):
    count = db.query(model).count()
    print(f"OK query {name}: {count}")


def main():
    print("DATABASE_URL:", os.environ["DATABASE_URL"])
    print("DIALECT:", engine.dialect.name)
    Base.metadata.create_all(bind=engine)
    ensure_lightweight_migrations()
    db = SessionLocal()
    try:
        seed_data(db)
        user = User(name="Smoke Farmer", phone="9000000001", password_hash=hash_password("secret123"), role="farmer")
        db.add(user); db.commit(); db.refresh(user)
        pest = db.query(Pest).first()
        assert pest, "Seed pests missing"
        det = Detection(user_id=user.id, image_path=str(ROOT / "README.md"), pest_id=pest.id, predicted_name=pest.common_name, confidence=0.9, ai_response={"ok": True})
        db.add(det)
        blog = BlogPost(title="Smoke Blog", summary="Test", body="<p>Hello</p>", author_name="QA")
        db.add(blog)
        event = PlatformEvent(title="Smoke Event", description="Test", event_date="2026-07-01")
        db.add(event)
        cal = CalendarEvent(month=1, title="Smoke Calendar", description="Test")
        db.add(cal)
        ins = InsecticideRecommendation(pest_id=pest.id, pest_name=pest.common_name, options=["option1"], note="test")
        db.add(ins)
        conv = ChatConversation(farmer_id=user.id, subject="Smoke Chat")
        db.add(conv); db.flush()
        db.add(ChatMessage(conversation_id=conv.id, sender_id=user.id, sender_role="farmer", message="hello"))
        db.add(FarmerNotification(user_id=user.id, title="Smoke", body="Notification"))
        db.add(UserFeedback(user_id=user.id, detection_id=det.id, is_correct=True))
        db.add(TrainingImage(image_path=str(ROOT / "README.md"), pest_id=pest.id, verified=True))
        db.add(TrainingJob(dataset_version="smoke"))
        db.add(AiKnowledgeItem(source_type="smoke", title="Smoke Knowledge", content="test"))
        db.add(PushNotificationCampaign(title="Smoke Push", body="test"))
        db.commit()
        db.add(BlogLike(blog_id=blog.id, user_id=user.id))
        db.add(BlogComment(blog_id=blog.id, user_id=user.id, comment="Nice"))
        db.commit()

        for model, name in [
            (User, "users"), (Pest, "pests"), (Detection, "detections"), (BlogPost, "blogs"),
            (BlogLike, "blog_likes"), (BlogComment, "blog_comments"), (PlatformEvent, "events"),
            (CalendarEvent, "calendar"), (InsecticideRecommendation, "insecticides"),
            (ChatConversation, "chat_conversations"), (ChatMessage, "chat_messages"),
            (FarmerNotification, "farmer_notifications"), (UserFeedback, "feedback"),
            (TrainingImage, "training_images"), (TrainingJob, "training_jobs"),
            (AiKnowledgeItem, "ai_knowledge"), (PushNotificationCampaign, "push_campaigns"),
        ]:
            assert_count(db, model, name)
        print("ALL_BACKEND_QUERY_SMOKE_TESTS_PASSED")
    finally:
        db.close()


if __name__ == "__main__":
    main()
