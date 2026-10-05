"""Model governance: statuses, deploy, rollback (upgrade step 7).

The backend ModelVersion table is the governance source of truth; the
ai-service filesystem registry holds the portable artifacts. Deployment is
always explicit and requires evaluation metrics to exist (no blind deploy).
"""
from __future__ import annotations

from datetime import datetime

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .models import ModelVersion

STATUSES = ["training", "testing", "approved", "production", "rejected", "archived"]
TRANSITIONS = {
    "training": {"testing", "rejected"},
    "testing": {"approved", "rejected"},
    "approved": {"rejected", "archived"},        # production only via deploy()
    "production": {"archived"},                  # demotion happens via deploy()/rollback()
    "rejected": set(),
    "archived": set(),                            # production again only via deploy() (rollback)
}


def _ai_activate(version: str) -> dict:
    r = requests.post(f"{settings.ai_service_url}/models/activate",
                      json={"version": version}, timeout=60)
    r.raise_for_status()
    return r.json()


def set_model_status(db: Session, row: ModelVersion, status: str, admin_id: str | None) -> ModelVersion:
    if status not in STATUSES:
        raise HTTPException(status_code=400, detail=f"Unknown status {status}")
    if status == "production":
        raise HTTPException(status_code=400, detail="Use deploy/rollback for production changes")
    if status not in TRANSITIONS.get(row.status, set()):
        raise HTTPException(status_code=400,
                            detail=f"Illegal transition {row.status} -> {status}")
    row.status = status
    row.updated_by = admin_id
    row.updated_at = datetime.utcnow()
    db.commit()
    return row


def deploy_model(db: Session, row: ModelVersion, admin_id: str | None,
                 require_comparison: bool = True) -> dict:
    """Approve-gated production deployment with automatic demotion + rollback
    trail. require_comparison=False is reserved for rollback: the target was
    already a validated production model, and rollback must stay available as
    the safety valve when the current production misbehaves."""
    if row.status not in ("approved", "archived"):
        raise HTTPException(status_code=400,
                            detail=f"Model must be approved or archived to deploy (status={row.status})")
    frozen_eval = (row.metrics or {}).get("frozen_eval") or {}
    if not frozen_eval.get("frozen_test"):
        raise HTTPException(status_code=400,
                            detail="Refusing deploy: no frozen-test evaluation recorded. Run POST /admin/ai/models/{id}/evaluate first.")
    current = db.query(ModelVersion).filter(ModelVersion.status == "production").first()
    if require_comparison and current and current.id != row.id:
        comp = (row.metrics or {}).get("comparison") or {}
        if comp.get("recommendation") != "deploy":
            raise HTTPException(status_code=400,
                                detail=f"Refusing deploy: comparison vs current production is "
                                       f"'{comp.get('recommendation') or 'missing'}'. "
                                       "A model that is worse on an important pest must not replace production.")
    try:
        _ai_activate(row.version)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI service refused activation: {exc}") from exc
    old = db.query(ModelVersion).filter(ModelVersion.status == "production").first()
    if old and old.id != row.id:
        old.status = "archived"
        old.was_production = True
        old.updated_by = admin_id
        old.updated_at = datetime.utcnow()
    row.status = "production"
    row.updated_by = admin_id
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"deployed": row.version, "previous": old.version if old and old.id != row.id else None}


def rollback_model(db: Session, admin_id: str | None, model_id: str | None = None) -> dict:
    """Redeploy the most recent previous production model (or an explicit one)."""
    if model_id:
        target = db.get(ModelVersion, model_id)
    else:
        target = (db.query(ModelVersion)
                  .filter(ModelVersion.was_production == True,
                          ModelVersion.status == "archived")
                  .order_by(ModelVersion.updated_at.desc()).first())
    if not target:
        raise HTTPException(status_code=404, detail="No rollback target found")
    return deploy_model(db, target, admin_id, require_comparison=False)
