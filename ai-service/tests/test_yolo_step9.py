"""Upgrade step 9 tests: bootstrap YOLO dataset builder, detector adoption of a
deployed YOLO registry model, optional MLflow tracking (real file store)."""
import os
import sys
import tempfile


STORE = tempfile.mkdtemp(prefix="cs-ms9-")
os.environ["MODEL_STORE"] = STORE
os.environ.setdefault("DINOV2_ENABLED", "false")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from app.yolo_train import CLASS_TO_IDX, build_yolo_dataset


def _img(path, color):
    arr = np.zeros((48, 48, 3), np.uint8)
    arr[:] = color
    Image.fromarray(arr).save(path)


def test_build_yolo_dataset_splits_and_labels(tmp_path):
    recs, splits = [], {}
    for i in range(4):
        p = tmp_path / f"psyllid-{i}.png"
        _img(p, (150, 60, 60))
        recs.append({"image_id": f"psyllid-{i}", "image_path": str(p), "pest_id": "citrus-psyllid"})
        splits[f"psyllid-{i}"] = "train" if i < 3 else "test"
    p = tmp_path / "neg-0.png"
    _img(p, (200, 200, 200))
    recs.append({"image_id": "neg-0", "image_path": str(p), "pest_id": "no-citrus-pest"})
    splits["neg-0"] = "val"

    out = tmp_path / "yolo"
    stats = build_yolo_dataset(recs, str(out), splits=splits)
    assert stats["written"] == 5 and stats["skipped"] == 0

    idx = CLASS_TO_IDX["citrus-psyllid"]
    label = next((out / "labels" / "train").glob("*.txt")).read_text().strip()
    assert label == f"{idx} 0.5 0.5 1.0 1.0"
    assert len(list((out / "images" / "test").glob("*.jpg"))) == 1   # frozen test separate
    assert len(list((out / "labels" / "val").glob("*.txt"))) == 1
    yaml_text = (out / "dataset.yaml").read_text()
    assert "names:" in yaml_text and "citrus-psyllid" in yaml_text
    assert "bootstrap" in yaml_text


def test_detector_adopts_deployed_yolo(tmp_path, monkeypatch):
    import app.detector as det
    import app.model_registry as reg
    dummy = tmp_path / "yolo_best.pt"
    dummy.write_bytes(b"stub")

    monkeypatch.setattr(reg, "active_model", lambda: {
        "architecture": "yolo11s", "checkpoint_path": str(dummy)})

    captured = {}

    class StubYOLO:
        def __init__(self, weights):
            captured["weights"] = weights

        def predict(self, *a, **k):
            return []

    monkeypatch.setattr(det, "YOLO", StubYOLO)
    d = det.Detector()
    img = np.zeros((100, 100, 3), np.uint8)
    boxes, meta = d.detect(img)
    assert meta["mode"] == "yolo11"
    assert captured["weights"] == str(dummy)


def test_detector_ignores_non_yolo_active(tmp_path, monkeypatch):
    import app.detector as det
    import app.model_registry as reg
    monkeypatch.setattr(reg, "active_model", lambda: {
        "architecture": "mobilenet_v3_small", "checkpoint_path": str(tmp_path / "x")})
    d = det.Detector()
    _, meta = d.detect(np.zeros((100, 100, 3), np.uint8))
    assert meta["mode"] == "opencv_fallback"


def test_mlflow_optional_tracking(tmp_path, monkeypatch):
    from app import tracking
    monkeypatch.setenv("MLFLOW_ENABLED", "false")
    assert tracking.track_training_run("r", {"a": 1}, {"acc": 0.9}) is False

    monkeypatch.setenv("MLFLOW_ENABLED", "true")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path}/mlflow.db")
    ok = tracking.track_training_run("r1", {"epochs": 3}, {"accuracy": 0.9, "macro_f1": 0.8},
                                     tags={"dataset_version": "v1"})
    assert ok is True
    assert (tmp_path / "mlflow.db").exists()
    ok2 = tracking.track_evaluation("e1", {"accuracy": 0.9, "per_class": {"x": {"recall": 1.0}}})
    assert ok2 is True


def test_train_yolo_needs_more_data(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    r = TestClient(app).post("/train/yolo", json={"dataset_version": "yv1", "records": []})
    assert r.status_code == 200
    assert r.json()["status"] == "needs_more_data"
