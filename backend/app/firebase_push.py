import json
import logging
import os
from functools import lru_cache
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception as import_exc:  # firebase-admin optional until installed
    firebase_admin = None
    credentials = None
    messaging = None
    _firebase_import_error = import_exc
else:
    _firebase_import_error = None

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "firebase_push.log"

logger = logging.getLogger("citrisurksha.firebase_push")
logger.setLevel(logging.INFO)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)


def mask_token(token: str | None) -> str:
    if not token:
        return "none"
    return f"{token[:10]}...{token[-6:]}" if len(token) > 20 else "short-token"


def credential_candidates() -> list[Path]:
    env_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    # User requested direct colocated file beside firebase_push.py.
    candidates.extend([
        BASE_DIR / "firebase-service-account.json",
        BASE_DIR.parent / "firebase-service-account.json",
        Path.cwd() / "backend" / "app" / "firebase-service-account.json",
        Path.cwd() / "backend" / "firebase-service-account.json",
        Path.cwd() / "firebase-service-account.json",
    ])
    # Keep order but remove duplicates.
    seen = set()
    unique = []
    for c in candidates:
        key = str(c.resolve()) if not c.is_absolute() else str(c)
        if key not in seen:
            unique.append(c)
            seen.add(key)
    return unique


@lru_cache(maxsize=1)
def firebase_app():
    if firebase_admin is None:
        logger.error("firebase-admin import failed: %s", _firebase_import_error)
        return None
    if firebase_admin._apps:
        app = list(firebase_admin._apps.values())[0]
        logger.info("Firebase app already initialized: %s", getattr(app, "name", "default"))
        return app

    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    try:
        if raw:
            logger.info("Initializing Firebase from FIREBASE_SERVICE_ACCOUNT_JSON")
            cred = credentials.Certificate(json.loads(raw))
            app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized from JSON env")
            return app

        tried = []
        for path in credential_candidates():
            tried.append(str(path))
            if path.exists():
                logger.info("Initializing Firebase from service account file: %s", path)
                cred = credentials.Certificate(str(path))
                app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully from %s", path)
                return app

        logger.error("Firebase service account not found. Tried: %s", tried)
        return None
    except Exception as exc:
        logger.exception("Firebase initialization failed: %s", exc)
        return None


def firebase_status() -> dict:
    app = firebase_app()
    candidates = [str(p) for p in credential_candidates()]
    existing = [str(p) for p in credential_candidates() if p.exists()]
    return {
        "firebase_admin_installed": firebase_admin is not None,
        "firebase_import_error": str(_firebase_import_error) if _firebase_import_error else None,
        "initialized": app is not None,
        "credential_candidates": candidates,
        "credential_files_found": existing,
        "log_file": str(LOG_FILE),
    }


def send_fcm_token(token: str, title: str, body: str, data: dict | None = None) -> dict:
    logger.info("Attempting FCM send token=%s title=%r", mask_token(token), title)
    app = firebase_app()
    if not app or messaging is None:
        reason = "firebase_admin_not_configured"
        logger.error("FCM send failed: %s status=%s", reason, firebase_status())
        return {"sent": False, "reason": reason, "debug": firebase_status()}
    try:
        msg = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(payload=messaging.APNSPayload(aps=messaging.Aps(sound="default"))),
        )
        res = messaging.send(msg)
        logger.info("FCM send success token=%s message_id=%s", mask_token(token), res)
        return {"sent": True, "message_id": res}
    except Exception as exc:
        logger.exception("FCM send failed token=%s error=%s", mask_token(token), exc)
        return {"sent": False, "reason": str(exc), "error_type": exc.__class__.__name__}
