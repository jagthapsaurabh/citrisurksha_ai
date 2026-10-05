"""Upgrade step 7 (backend): ModelVersion governance - transitions, deploy
gate, demotion and rollback."""
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite://")  # import-safe, no postgres needed

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db import Base  # noqa: E402
from app.models import ModelVersion  # noqa: E402
from app import model_governance as gov  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def mk(s, version, status, metrics=None, was_production=False):
    row = ModelVersion(version=version, status=status, metrics=metrics or {},
                       was_production=was_production, architecture="mobilenet_v3_small")
    s.add(row)
    s.commit()
    return row


def test_status_transitions(db):
    m = mk(db, "v-t1", "training")
    with pytest.raises(HTTPException):
        gov.set_model_status(db, m, "approved", "admin")       # training->approved illegal
    with pytest.raises(HTTPException):
        gov.set_model_status(db, m, "production", "admin")     # only via deploy
    gov.set_model_status(db, m, "testing", "admin")
    gov.set_model_status(db, m, "approved", "admin")
    gov.set_model_status(db, m, "rejected", "admin")
    with pytest.raises(HTTPException):
        gov.set_model_status(db, m, "testing", "admin")        # rejected is terminal


def test_deploy_requires_metrics_and_demotes_old(db, monkeypatch):
    monkeypatch.setattr(gov, "_ai_activate", lambda version: {"status": "activated"})
    old = mk(db, "v-old", "production", metrics={"frozen_eval": {"frozen_test": True, "accuracy": 0.8}})
    new = mk(db, "v-new", "approved")                          # no metrics
    with pytest.raises(HTTPException):
        gov.deploy_model(db, new, "admin")                     # refuse blind deploy
    new.metrics = {"frozen_eval": {"frozen_test": True, "accuracy": 0.91, "macro_f1": 0.9},
                 "comparison": {"recommendation": "deploy"}}
    db.commit()
    out = gov.deploy_model(db, new, "admin")
    assert out["deployed"] == "v-new" and out["previous"] == "v-old"
    assert new.status == "production"
    assert old.status == "archived" and old.was_production is True


def test_rollback_restores_previous_production(db, monkeypatch):
    monkeypatch.setattr(gov, "_ai_activate", lambda version: {"status": "activated"})
    old = mk(db, "v-old", "archived", metrics={"frozen_eval": {"frozen_test": True, "accuracy": 0.8}}, was_production=True)
    mk(db, "v-cur", "production", metrics={"frozen_eval": {"frozen_test": True, "accuracy": 0.9}})
    out = gov.rollback_model(db, "admin")
    assert out["deployed"] == "v-old"
    assert old.status == "production"


def test_list_models_endpoint_shape(db, monkeypatch):
    import app.routers.admin as admin_mod
    monkeypatch.setattr(admin_mod, "requests", type("R", (), {
        "get": staticmethod(lambda *a, **k: (_ for _ in ()).throw(OSError("down")))}))
    mk(db, "v-a", "testing", metrics={"accuracy": 0.7})
    ns = type("A", (), {"id": "admin"})()
    out = admin_mod.list_ai_models(db=db, _admin=ns)
    assert out["active"] == {}
    assert out["models"][0]["version"] == "v-a" and out["models"][0]["status"] == "testing"


def test_deploy_blocked_when_comparison_rejects(db, monkeypatch):
    monkeypatch.setattr(gov, "_ai_activate", lambda version: {"status": "activated"})
    mk(db, "v-prod", "production", metrics={"frozen_eval": {"frozen_test": True, "accuracy": 0.9}})
    cand = mk(db, "v-cand", "approved", metrics={
        "frozen_eval": {"frozen_test": True, "accuracy": 0.95},
        "comparison": {"recommendation": "reject"}})
    with pytest.raises(HTTPException):
        gov.deploy_model(db, cand, "admin")
    cand.metrics["comparison"] = {"recommendation": "manual_review"}
    with pytest.raises(HTTPException):
        gov.deploy_model(db, cand, "admin")
