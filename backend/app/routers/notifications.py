from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..firebase_push import LOG_FILE, firebase_status, send_fcm_token
from ..models import AdminNotification, FarmerNotification, PushNotificationCampaign, User
from ..schemas import FcmTokenIn, NotificationIn
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/notifications", tags=["notifications"])


def notif_payload(n: FarmerNotification):
    return {"id": n.id, "title": n.title, "body": n.body, "data": n.data, "status": n.status, "is_read": n.is_read, "created_at": n.created_at}

def admin_notif_payload(n: AdminNotification):
    return {"id": n.id, "title": n.title, "body": n.body, "data": n.data, "is_read": n.is_read, "created_at": n.created_at}


def create_and_send(db: Session, user: User | None, title: str, body: str, data: dict | None = None):
    resp = {}
    status = "stored"
    if user and user.fcm_token:
        resp = send_fcm_token(user.fcm_token, title, body, data or {})
        status = "sent" if resp.get("sent") else "stored_push_failed"
    elif user:
        status = "stored_no_token"
    n = FarmerNotification(user_id=user.id if user else None, title=title, body=body, data=data or {}, status=status, fcm_response=resp)
    db.add(n)
    return n

@router.post("/register-token")
def register_token(payload: FcmTokenIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.token or len(payload.token) < 10:
        raise HTTPException(status_code=400, detail="Invalid FCM token")
    user.fcm_token = payload.token
    user.fcm_platform = payload.platform
    user.fcm_token_updated_at = datetime.utcnow()
    db.commit()
    return {"status": "token_saved"}

@router.get("")
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(FarmerNotification).filter((FarmerNotification.user_id == user.id) | (FarmerNotification.user_id == None)).order_by(FarmerNotification.created_at.desc()).limit(100).all()
    return [notif_payload(r) for r in rows]

@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.query(FarmerNotification).filter(((FarmerNotification.user_id == user.id) | (FarmerNotification.user_id == None)), FarmerNotification.is_read == False).count()
    return {"count": count}

@router.post("/{notification_id}/read")
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(FarmerNotification, notification_id)
    if not row or (row.user_id not in {None, user.id}):
        raise HTTPException(status_code=404, detail="Notification not found")
    row.is_read = True
    db.commit()
    return {"status": "read"}

@router.delete("/{notification_id}")
def delete_notification(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(FarmerNotification, notification_id)
    if not row or row.user_id != user.id:
        if row and row.user_id is None:
            row.is_read = True; db.commit(); return {"status": "cleared"}
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}

@router.post("/clear")
def clear_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(FarmerNotification).filter((FarmerNotification.user_id == user.id) | (FarmerNotification.user_id == None)).all()
    for r in rows:
        r.is_read = True
    db.commit()
    return {"status": "cleared", "count": len(rows)}

@router.get("/admin/firebase-status")
def admin_firebase_status(_admin: User = Depends(require_admin)):
    return firebase_status()

@router.get("/admin/firebase-logs")
def admin_firebase_logs(lines: int = 100, _admin: User = Depends(require_admin)):
    try:
        if not LOG_FILE.exists():
            return {"log_file": str(LOG_FILE), "lines": []}
        content = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        return {"log_file": str(LOG_FILE), "lines": content[-max(1, min(lines, 500)):]}
    except Exception as exc:
        return {"log_file": str(LOG_FILE), "error": str(exc), "lines": []}

@router.get("/admin")
def admin_notifications(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(AdminNotification).order_by(AdminNotification.created_at.desc()).limit(300).all()
    return [admin_notif_payload(r) for r in rows]

@router.get("/admin/unread-count")
def admin_unread_count(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return {"count": db.query(AdminNotification).filter(AdminNotification.is_read == False).count()}

@router.post("/admin/{notification_id}/read")
def admin_mark_read(notification_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(AdminNotification, notification_id)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.is_read = True
    db.commit()
    return {"status": "read"}

@router.delete("/admin/{notification_id}")
def admin_delete_notification(notification_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    row = db.get(AdminNotification, notification_id)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}

@router.post("/admin/clear")
def admin_clear_notifications(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(AdminNotification).all()
    for r in rows:
        r.is_read = True
    db.commit()
    return {"status": "cleared", "count": len(rows)}

@router.post("/admin/send")
def admin_send(payload: NotificationIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = [db.get(User, payload.user_id)] if payload.user_id else db.query(User).filter(User.role == "farmer").all()
    users = [u for u in users if u]
    sent = []
    sent_count = 0
    failed_count = 0
    for u in users:
        n = create_and_send(db, u, payload.title, payload.body, payload.data)
        if n.status == "sent": sent_count += 1
        else: failed_count += 1
        sent.append({"user_id": u.id, "notification_id": n.id, "status": n.status})
    campaign = PushNotificationCampaign(title=payload.title, body=payload.body, target=payload.user_id or "all_farmers", sent_count=sent_count, failed_count=failed_count, data=payload.data, created_by=admin.id)
    db.add(campaign)
    db.commit()
    return {"status": "queued", "campaign_id": campaign.id, "count": len(sent), "sent_count": sent_count, "failed_count": failed_count, "items": sent}

@router.get("/admin/push-campaigns")
def push_campaigns(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    rows = db.query(PushNotificationCampaign).order_by(PushNotificationCampaign.created_at.desc()).limit(300).all()
    return [{"id": r.id, "title": r.title, "body": r.body, "target": r.target, "sent_count": r.sent_count, "failed_count": r.failed_count, "data": r.data, "created_by": r.created_by, "created_at": r.created_at} for r in rows]
