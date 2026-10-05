import os
from fastapi import HTTPException
from .config import settings


def image_url_for_path(path: str | None) -> str | None:
    if not path:
        return None
    try:
        rel = os.path.relpath(path, settings.upload_dir).replace(os.sep, "/")
        if rel.startswith(".."):
            return None
        return f"/media/{rel}"
    except Exception:
        return None


def safe_media_path(file_path: str) -> str:
    root = os.path.abspath(settings.upload_dir)
    full = os.path.abspath(os.path.join(root, file_path))
    if not full.startswith(root) or not os.path.exists(full):
        raise HTTPException(status_code=404, detail="File not found")
    return full
