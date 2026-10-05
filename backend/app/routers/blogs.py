from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..admin_notify import create_admin_notification
from ..cache import get_json, set_json
from ..db import get_db
from ..models import BlogComment, BlogLike, BlogPost, User
from ..security import get_current_user

router = APIRouter(prefix="/blogs", tags=["blogs"])

class CommentIn(BaseModel):
    comment: str

def blog_payload(p: BlogPost, db: Session | None = None, user: User | None = None):
    data = {"id": p.id, "title": p.title, "summary": p.summary, "body": p.body, "language": p.language, "image_url": p.image_url, "doc_url": p.doc_url, "content_type": p.content_type, "author_name": p.author_name, "views_count": p.views_count or 0, "created_at": p.created_at}
    if db:
        data["likes_count"] = db.query(BlogLike).filter(BlogLike.blog_id == p.id).count()
        data["comments_count"] = db.query(BlogComment).filter(BlogComment.blog_id == p.id).count()
        data["liked_by_me"] = bool(user and db.query(BlogLike).filter(BlogLike.blog_id == p.id, BlogLike.user_id == user.id).first())
    return data

@router.get("")
def list_blogs(language: str = "en", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cache_key = f"blogs:{language}:{user.id}"
    cached = get_json(cache_key)
    if cached:
        return cached
    posts = db.query(BlogPost).filter(BlogPost.published == True, BlogPost.language == language).order_by(BlogPost.created_at.desc()).limit(50).all()
    if not posts and language != "en":
        posts = db.query(BlogPost).filter(BlogPost.published == True, BlogPost.language == "en").order_by(BlogPost.created_at.desc()).limit(50).all()
    result = [blog_payload(p, db, user) for p in posts]
    set_json(cache_key, result, ttl=120)
    return result

@router.get("/{blog_id}")
def get_blog(blog_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.get(BlogPost, blog_id)
    if not post or not post.published:
        raise HTTPException(status_code=404, detail="Blog post not found")
    post.views_count = (post.views_count or 0) + 1
    db.commit()
    data = blog_payload(post, db, user)
    comments = db.query(BlogComment).filter(BlogComment.blog_id == blog_id).order_by(BlogComment.created_at.desc()).limit(100).all()
    data["comments"] = [{"id": c.id, "user_id": c.user_id, "comment": c.comment, "created_at": c.created_at} for c in comments]
    return data

@router.post("/{blog_id}/like")
def toggle_like(blog_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.get(BlogPost, blog_id):
        raise HTTPException(status_code=404, detail="Blog post not found")
    like = db.query(BlogLike).filter(BlogLike.blog_id == blog_id, BlogLike.user_id == user.id).first()
    if like:
        db.delete(like); liked = False
    else:
        db.add(BlogLike(blog_id=blog_id, user_id=user.id)); liked = True
    db.commit()
    return {"liked": liked, "likes_count": db.query(BlogLike).filter(BlogLike.blog_id == blog_id).count()}

@router.post("/{blog_id}/comments")
def add_comment(blog_id: str, payload: CommentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.comment.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    if not db.get(BlogPost, blog_id):
        raise HTTPException(status_code=404, detail="Blog post not found")
    row = BlogComment(blog_id=blog_id, user_id=user.id, comment=payload.comment.strip())
    db.add(row)
    create_admin_notification(db, "New blog comment", f"{user.name} commented on a blog.", {"type": "blog_comment", "blog_id": blog_id, "user_id": user.id})
    db.commit()
    return {"status": "comment_added", "comment_id": row.id}
