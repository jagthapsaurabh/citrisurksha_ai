from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..admin_notify import create_admin_notification
from ..db import get_db, SessionLocal
from ..media import image_url_for_path
from ..models import ChatConversation, ChatMessage, User
from .detections import save_upload
from ..schemas import ChatMessageIn
from ..security import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


def save_chat_file(file: UploadFile) -> tuple[str, str, str]:
    import os, uuid
    from ..config import settings
    content = file.file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large; max 20MB")
    folder = os.path.join(settings.upload_dir, "chat")
    os.makedirs(folder, exist_ok=True)
    ext = os.path.splitext(file.filename or "file.bin")[1]
    path = os.path.join(folder, f"{uuid.uuid4()}{ext}")
    with open(path, "wb") as f:
        f.write(content)
    return path, file.filename or "attachment", file.content_type or "application/octet-stream"

class ChatManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = {}
    async def connect(self, conversation_id: str, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(conversation_id, []).append(ws)
    def disconnect(self, conversation_id: str, ws: WebSocket):
        if conversation_id in self.rooms and ws in self.rooms[conversation_id]:
            self.rooms[conversation_id].remove(ws)
    async def broadcast(self, conversation_id: str, payload: dict):
        dead=[]
        for ws in self.rooms.get(conversation_id, []):
            try: await ws.send_json(payload)
            except Exception: dead.append(ws)
        for ws in dead: self.disconnect(conversation_id, ws)
manager = ChatManager()

async def broadcast_message(conversation_id: str, row: ChatMessage):
    await manager.broadcast(conversation_id, {"id": row.id, "conversation_id": conversation_id, "sender_role": row.sender_role, "message": row.message, "attachment_url": row.attachment_url, "attachment_name": row.attachment_name, "attachment_type": row.attachment_type, "created_at": str(row.created_at)})

@router.websocket("/ws/{conversation_id}")
async def chat_ws(ws: WebSocket, conversation_id: str):
    await manager.connect(conversation_id, ws)
    try:
        while True:
            await ws.receive_text()  # keepalive/client typing ignored for now
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, ws)

@router.get("/conversations")
def my_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ChatConversation).filter(ChatConversation.farmer_id == user.id).order_by(ChatConversation.created_at.desc()).all()
    return [{"id": c.id, "subject": c.subject, "status": c.status, "assigned_to": c.assigned_to, "created_at": c.created_at} for c in rows]

@router.post("/conversations")
async def create_conversation(payload: ChatMessageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = ChatConversation(farmer_id=user.id, subject="Farmer support")
    db.add(conv); db.flush()
    msg = ChatMessage(conversation_id=conv.id, sender_id=user.id, sender_role="farmer", message=payload.message)
    db.add(msg)
    create_admin_notification(db, "New farmer chat", f"{user.name} started a chat: {payload.message[:120]}", {"type": "chat", "conversation_id": conv.id, "user_id": user.id})
    db.commit(); db.refresh(msg)
    await broadcast_message(conv.id, msg)
    return {"status": "created", "conversation_id": conv.id}

@router.get("/conversations/{conversation_id}/messages")
def messages(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = db.get(ChatConversation, conversation_id)
    if not conv or conv.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    rows = db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at).all()
    return [{"id": m.id, "sender_role": m.sender_role, "message": m.message, "attachment_url": m.attachment_url, "attachment_name": m.attachment_name, "attachment_type": m.attachment_type, "created_at": m.created_at} for m in rows]

@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, payload: ChatMessageIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = db.get(ChatConversation, conversation_id)
    if not conv or conv.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    row = ChatMessage(conversation_id=conversation_id, sender_id=user.id, sender_role="farmer", message=payload.message)
    db.add(row)
    create_admin_notification(db, "New farmer chat message", f"{user.name}: {payload.message[:120]}", {"type": "chat", "conversation_id": conversation_id, "user_id": user.id})
    db.commit(); db.refresh(row)
    await broadcast_message(conversation_id, row)
    return {"status": "sent", "message_id": row.id}

@router.post("/conversations/{conversation_id}/attachments")
async def send_attachment(conversation_id: str, message: str = Form(""), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = db.get(ChatConversation, conversation_id)
    if not conv or conv.farmer_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    path, name, ctype = save_chat_file(file)
    row = ChatMessage(conversation_id=conversation_id, sender_id=user.id, sender_role="farmer", message=message or name, attachment_url=image_url_for_path(path), attachment_name=name, attachment_type=ctype)
    db.add(row)
    create_admin_notification(db, "New farmer chat attachment", f"{user.name} sent attachment: {name}", {"type": "chat", "conversation_id": conversation_id, "user_id": user.id})
    db.commit(); db.refresh(row)
    await broadcast_message(conversation_id, row)
    return {"status": "sent", "message_id": row.id, "attachment_url": row.attachment_url}
