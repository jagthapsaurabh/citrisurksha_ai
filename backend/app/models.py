import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def uid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="farmer")
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    acres_land: Mapped[float | None] = mapped_column(Float, nullable=True)
    plants: Mapped[str | None] = mapped_column(Text, nullable=True)
    citrus_varieties: Mapped[str | None] = mapped_column(Text, nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    farming_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    fcm_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    fcm_platform: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fcm_token_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Pest(Base):
    __tablename__ = "pests"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    common_name: Mapped[str] = mapped_column(String(180), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scientific_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    category: Mapped[str] = mapped_column(String(40), default="insect")
    lifecycle: Mapped[dict] = mapped_column(JSON, default=dict)
    symptoms: Mapped[str] = mapped_column(Text, default="")
    prevention: Mapped[str] = mapped_column(Text, default="")
    cure: Mapped[str] = mapped_column(Text, default="")
    organic_control: Mapped[str] = mapped_column(Text, default="")
    chemical_control: Mapped[str] = mapped_column(Text, default="")
    safety_note: Mapped[str] = mapped_column(Text, default="Follow local agriculture department guidance before pesticide use.")
    translations: Mapped[dict] = mapped_column(JSON, default=dict)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    image_path: Mapped[str] = mapped_column(String(500))
    pest_id: Mapped[str | None] = mapped_column(ForeignKey("pests.id"), nullable=True, index=True)
    predicted_name: Mapped[str] = mapped_column(String(180))
    confidence: Mapped[float] = mapped_column(Float, default=0)
    stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="gallery")
    ai_response: Mapped[dict] = mapped_column(JSON, default=dict)
    admin_status: Mapped[str] = mapped_column(String(30), default="unreviewed")
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User")
    pest = relationship("Pest")

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(220))
    summary: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="en")
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    doc_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str] = mapped_column(String(20), default="html")
    author_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    month: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(120), default="India")

class InsecticideRecommendation(Base):
    __tablename__ = "insecticide_recommendations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    pest_id: Mapped[str] = mapped_column(String, index=True)
    pest_name: Mapped[str] = mapped_column(String(180))
    options: Mapped[list] = mapped_column(JSON, default=list)
    note: Mapped[str] = mapped_column(Text, default="")
    disclaimer: Mapped[str] = mapped_column(Text, default="Use only CIB-RC registered products for citrus and follow label instructions.")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminNotification(Base):
    __tablename__ = "admin_notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(220))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PushNotificationCampaign(Base):
    __tablename__ = "push_notification_campaigns"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(220))
    body: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(String(80), default="all_farmers")
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class FarmerNotification(Base):
    __tablename__ = "farmer_notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(220))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="stored")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    fcm_response: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BlogLike(Base):
    __tablename__ = "blog_likes"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    blog_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BlogComment(Base):
    __tablename__ = "blog_comments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    blog_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PlatformEvent(Base):
    __tablename__ = "platform_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(220))
    description: Mapped[str] = mapped_column(Text)
    event_date: Mapped[str] = mapped_column(String(40))
    region: Mapped[str] = mapped_column(String(120), default="India")
    send_notification: Mapped[bool] = mapped_column(Boolean, default=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    farmer_id: Mapped[str] = mapped_column(String, index=True)
    assigned_to: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    subject: Mapped[str] = mapped_column(String(220), default="Farmer support")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    sender_id: Mapped[str | None] = mapped_column(String, nullable=True)
    sender_role: Mapped[str] = mapped_column(String(30), default="farmer")
    message: Mapped[str] = mapped_column(Text)
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attachment_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TrainingImage(Base):
    __tablename__ = "training_images"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    image_path: Mapped[str] = mapped_column(String(500))
    pest_id: Mapped[str] = mapped_column(String, index=True)
    stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(80), default="admin")
    detection_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    detection_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_pest_id: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AiKnowledgeItem(Base):
    __tablename__ = "ai_knowledge_items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    source_type: Mapped[str] = mapped_column(String(40), default="admin")
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    pest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TrainingJob(Base):
    __tablename__ = "training_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    dataset_version: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_job_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DatasetVersion(Base):
    """Immutable dataset snapshot metadata (upgrade step 7)."""
    __tablename__ = "dataset_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    version: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    annotation_version: Mapped[str] = mapped_column(String(40), default="v1")
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    class_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    train_count: Mapped[int] = mapped_column(Integer, default=0)
    val_count: Mapped[int] = mapped_column(Integer, default=0)
    test_count: Mapped[int] = mapped_column(Integer, default=0)
    frozen_test_ids: Mapped[list] = mapped_column(JSON, default=list)
    dups_removed: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ModelVersion(Base):
    """Governed model registry (upgrade step 7): statuses
    training/testing/approved/production/rejected/archived + rollback."""
    __tablename__ = "model_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    version: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    architecture: Mapped[str] = mapped_column(String(80), default="mobilenet_v3_small")
    dataset_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    checkpoint_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    torchscript_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    labels: Mapped[list] = mapped_column(JSON, default=list)
    image_size: Mapped[int] = mapped_column(Integer, default=224)
    training_config: Mapped[dict] = mapped_column(JSON, default=dict)
    environment: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="training", index=True)
    was_production: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
