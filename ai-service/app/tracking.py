"""Optional MLflow experiment tracking (upgrade step 9).

Self-hosted MLflow (any tracking URI: http server, sqlite, or plain file store)
wraps training and evaluation for observability. It is OPTIONAL BY DESIGN:
production inference and training never depend on it - every call is a no-op
when disabled, uninstalled or unreachable, and failures only log a warning.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger("citrisurksha.tracking")

try:
    import mlflow
except Exception:  # pragma: no cover - optional dependency
    mlflow = None


def mlflow_enabled() -> bool:
    return (os.getenv("MLFLOW_ENABLED", "false").strip().lower() in {"1", "true", "yes"}
            and mlflow is not None)


def _configure() -> None:
    uri = os.getenv("MLFLOW_TRACKING_URI", "").strip() or None
    if uri:
        mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT", "citrisurksha-training"))


def track_training_run(run_name: str, params: dict, metrics: dict,
                       artifacts: dict | None = None, tags: dict | None = None) -> bool:
    """Best-effort tracking; returns True only when something was recorded."""
    if not mlflow_enabled():
        return False
    try:
        _configure()
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params(_flat(params))
            mlflow.log_metrics(_numeric(metrics))
            for k, v in (tags or {}).items():
                mlflow.set_tag(k, str(v))
            for name, path in (artifacts or {}).items():
                if path and os.path.exists(path):
                    mlflow.log_artifact(path, artifact_path=name)
        return True
    except Exception as exc:
        log.warning("MLflow tracking skipped (non-fatal): %s", exc)
        return False


def track_evaluation(run_name: str, report: dict, tags: dict | None = None) -> bool:
    if not mlflow_enabled():
        return False
    try:
        _configure()
        with mlflow.start_run(run_name=run_name):
            flat = _numeric(_flatten(report, prefix=""))
            mlflow.log_metrics(flat)
            for k, v in (tags or {}).items():
                mlflow.set_tag(k, str(v))
        return True
    except Exception as exc:
        log.warning("MLflow evaluation tracking skipped (non-fatal): %s", exc)
        return False


def _flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flat(v, prefix=f"{key}."))
        else:
            out[key] = v
    return out


def _numeric(d: dict) -> dict:
    return {k: float(v) for k, v in d.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)}


def _flatten(d: dict, prefix: str) -> dict:
    return _flat(d, prefix)
