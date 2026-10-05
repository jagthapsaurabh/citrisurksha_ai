from sqlalchemy.orm import Session
from .models import AdminNotification


def create_admin_notification(db: Session, title: str, body: str, data: dict | None = None) -> AdminNotification:
    row = AdminNotification(title=title, body=body, data=data or {})
    db.add(row)
    return row
