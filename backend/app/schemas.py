from datetime import datetime
from pydantic import BaseModel

class RegisterIn(BaseModel):
    name: str
    phone: str
    password: str
    confirm_password: str | None = None
    district: str | None = None
    language: str = "en"

class LoginIn(BaseModel):
    phone: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str

class UserProfileOut(BaseModel):
    id: str
    name: str
    phone: str
    role: str
    district: str | None = None
    language: str = "en"
    email: str | None = None
    village: str | None = None
    state: str | None = None
    address: str | None = None
    acres_land: float | None = None
    plants: str | None = None
    citrus_varieties: str | None = None
    irrigation_type: str | None = None
    farming_experience_years: int | None = None
    profile_completed: bool = False
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    name: str | None = None
    district: str | None = None
    language: str | None = None
    email: str | None = None
    village: str | None = None
    state: str | None = None
    address: str | None = None
    acres_land: float | None = None
    plants: str | None = None
    citrus_varieties: str | None = None
    irrigation_type: str | None = None
    farming_experience_years: int | None = None

class PestIn(BaseModel):
    id: str
    common_name: str
    scientific_name: str | None = None
    category: str = "insect"
    lifecycle: dict = {}
    symptoms: str = ""
    prevention: str = ""
    cure: str = ""
    organic_control: str = ""
    chemical_control: str = ""
    safety_note: str = "Follow local agriculture department guidance before pesticide use."
    translations: dict = {}
    image_url: str | None = None

class PestOut(PestIn):
    updated_at: datetime | None = None
    class Config:
        from_attributes = True

class DetectionUpdate(BaseModel):
    pest_id: str | None = None
    predicted_name: str | None = None
    confidence: float | None = None
    stage: str | None = None
    admin_status: str | None = "corrected"
    admin_note: str | None = None

class CalendarEventIn(BaseModel):
    month: int
    title: str
    description: str
    region: str = "India"
    translations: dict = {}

class FcmTokenIn(BaseModel):
    token: str
    platform: str = "unknown"

class NotificationIn(BaseModel):
    title: str
    body: str
    user_id: str | None = None
    data: dict = {}

class InsecticideIn(BaseModel):
    pest_id: str
    pest_name: str
    options: list[str] = []
    note: str = ""
    disclaimer: str = "Use only CIB-RC registered products for citrus and follow label instructions."
    is_active: bool = True

class FeedbackIn(BaseModel):
    is_correct: bool | None = None
    corrected_pest_id: str | None = None
    comment: str | None = None

class AiKnowledgeIn(BaseModel):
    source_type: str = "admin"
    title: str
    content: str = ""
    url: str | None = None
    pest_id: str | None = None
    metadata: dict = {}

class TrainingRequest(BaseModel):
    dataset_version: str
    base_model: str = "mobilenet_v3_small"
    epochs: int = 3
    batch_size: int = 8
    min_accuracy_gate: float = 0.75
    classes: list[dict] = []
    training_records: list[dict] = []
    knowledge_records: list[dict] = []

class BlogIn(BaseModel):
    title: str
    summary: str = ""
    body: str
    language: str = "en"
    published: bool = True
    image_url: str | None = None
    doc_url: str | None = None
    content_type: str = "html"
    author_name: str | None = None
    translations: dict = {}

class AdminUserIn(BaseModel):
    name: str
    phone: str
    password: str
    role: str = "agronomist"
    district: str | None = None
    email: str | None = None

class ResetPasswordIn(BaseModel):
    new_password: str

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str | None = None

class AdminUserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    role: str | None = None
    district: str | None = None
    email: str | None = None
    is_active: bool | None = None

class PlatformEventIn(BaseModel):
    title: str
    description: str
    event_date: str
    region: str = "India"
    send_notification: bool = True
    published: bool = True
    translations: dict = {}

class ChatMessageIn(BaseModel):
    message: str
