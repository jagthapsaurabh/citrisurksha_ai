"""Step 12: runnable security checklist.

  python3 scripts/security_check.py

Exits non-zero if any check fails. Covers: tracked-secret scan, upload limits,
path traversal, auth enforcement, and AI diagnostics info-leak checks.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/cs-security-check.db")
os.environ.setdefault("MODEL_STORE", tempfile.mkdtemp(prefix="cs-sec-"))
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ai-service"))

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def main() -> int:
    # 1. no tracked secrets
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                           text=True).stdout.splitlines()
    bases = {f: os.path.basename(f) for f in files}
    bad = [f for f in files if ("firebase-service-account" in f or "adminsdk" in f)]
    check("no firebase admin/service-account files tracked", not bad, ",".join(bad))
    envs = [f for f in files if bases[f] == ".env" or
            (bases[f].startswith(".env.") and "example" not in bases[f])]
    check("no .env files tracked (.env.example templates allowed)", not envs, ",".join(envs))

    # 2. upload size limit (20 MB) + traversal
    try:
        from fastapi import UploadFile
        from app.routers.detections import save_upload
        import io
        try:
            save_upload(UploadFile(filename="x.jpg", file=io.BytesIO(b"j" * (21 * 1024 * 1024))))
            check("upload >20MB rejected", False)
        except Exception:
            check("upload >20MB rejected", True)
    except Exception as exc:
        check("upload >20MB rejected", False, str(exc))

    from app.media import safe_media_path
    try:
        safe_media_path("../../etc/passwd")
        check("path traversal blocked", False)
    except Exception:
        check("path traversal blocked", True)

    # 3. auth enforcement on admin API
    from fastapi.testclient import TestClient
    from app.main import app as backend_app
    with TestClient(backend_app) as client:
        r = client.get("/admin/dashboard")
        check("admin API requires auth", r.status_code in (401, 403), f"HTTP {r.status_code}")
        r2 = client.get("/detections/history")
        check("farmer API requires auth", r2.status_code in (401, 403), f"HTTP {r2.status_code}")

    # 4. AI diagnostics leak check
    from app.main import app as ai_app
    with TestClient(ai_app) as client:
        info = client.get("/pipeline/info").json()
        blob = json_dumps(info)
        leak = [k for k in ("api_key", "password", "service_account", "secret",
                            "/app/model-store", "QDRANT_API_KEY") if k in blob.lower()]
        check("pipeline info leaks no credentials/paths", not leak, ",".join(leak))

    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    return 1 if failed else 0


def json_dumps(x) -> str:
    import json
    return json.dumps(x)


if __name__ == "__main__":
    raise SystemExit(main())
