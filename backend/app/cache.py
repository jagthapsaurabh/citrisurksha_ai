import json
import logging
import time
import redis
from .config import settings

logger = logging.getLogger("citrisurksha.cache")
_client = None
_memory_cache: dict[str, tuple[float, str]] = {}

def redis_client():
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
    return _client

def _memory_get(key: str):
    row = _memory_cache.get(key)
    if not row:
        return None
    expires, value = row
    if expires < time.time():
        _memory_cache.pop(key, None)
        return None
    return value

def _memory_set(key: str, value: str, ttl: int):
    # keep memory fallback bounded
    if len(_memory_cache) > 1000:
        _memory_cache.clear()
    _memory_cache[key] = (time.time() + ttl, value)

def get_json(key: str):
    try:
        value = redis_client().get(key)
        if value:
            return json.loads(value)
    except Exception as exc:
        logger.debug("Redis get failed for %s: %s", key, exc)
    try:
        value = _memory_get(key)
        return json.loads(value) if value else None
    except Exception:
        return None

def set_json(key: str, value, ttl: int = 600):
    payload = json.dumps(value, default=str)
    try:
        redis_client().setex(key, ttl, payload)
        return
    except Exception as exc:
        logger.debug("Redis set failed for %s: %s", key, exc)
    _memory_set(key, payload, ttl)

def delete_key(key: str):
    _memory_cache.pop(key, None)
    try:
        redis_client().delete(key)
    except Exception:
        pass

def delete_pattern(pattern: str):
    try:
        client = redis_client()
        for key in client.scan_iter(pattern):
            client.delete(key)
    except Exception:
        pass
    # simple memory wildcard support for prefix*
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        for key in list(_memory_cache):
            if key.startswith(prefix):
                _memory_cache.pop(key, None)
