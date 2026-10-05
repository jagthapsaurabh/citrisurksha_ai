import io
import json
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from PIL import Image, UnidentifiedImageError
from .ml import inference_engine, train_classifier
from .model_registry import active_model
from .schemas import KnowledgeIn, Prediction, TrainingRequest

app = FastAPI(title="CitriSurksha AI Service", version="1.0.0", default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=1024)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail, "service": "ai-service", "path": str(request.url.path)})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"success": False, "error": "AI service internal error", "detail": str(exc), "service": "ai-service", "path": str(request.url.path)})

MODEL_STORE = os.getenv("MODEL_STORE", "/app/model-store")
KNOWLEDGE_FILE = os.path.join(MODEL_STORE, "knowledge.jsonl")


def ensure_store():
    os.makedirs(MODEL_STORE, exist_ok=True)
    os.makedirs(os.path.join(MODEL_STORE, "jobs"), exist_ok=True)
    # Bootstrap bundled scientific documentation, including the user-provided PDF extraction.
    bundled = "/app/training-data/citrus_pests_pdf_knowledge.jsonl"
    if os.path.exists(bundled):
        existing = set()
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                        existing.add((row.get("source_type"), row.get("title"), row.get("pest_id")))
                    except Exception:
                        pass
        with open(KNOWLEDGE_FILE, "a", encoding="utf-8") as out, open(bundled, "r", encoding="utf-8") as src:
            for line in src:
                try:
                    row = json.loads(line)
                    key = (row.get("source_type"), row.get("title"), row.get("pest_id"))
                    if key not in existing:
                        row.setdefault("created_at", datetime.utcnow().isoformat())
                        out.write(json.dumps(row, ensure_ascii=False) + "\n")
                        existing.add(key)
                except Exception:
                    pass


def append_knowledge(item: dict):
    ensure_store()
    with open(KNOWLEDGE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def read_knowledge(limit: int = 500) -> list[dict]:
    ensure_store()
    if not os.path.exists(KNOWLEDGE_FILE):
        return []
    rows = []
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows[-limit:]


@app.get("/health")
def health():
    meta = active_model()
    return {
        "status": "healthy",
        "service": "citrisurksha-ai",
        "framework": "pytorch/torchvision",
        "active_model": meta.get("version"),
        "model_status": meta.get("status"),
        "architecture": meta.get("architecture"),
        "checkpoint_registered": bool(meta.get("checkpoint_path")),
        "paid_ai_services": False,
    }


@app.get("/models/active")
def model_info():
    return active_model()


@app.get("/models/versions")
def model_versions():
    from .model_registry import list_versions
    return {"versions": list_versions(), "active": active_model().get("version")}


@app.post("/models/activate")
def model_activate(payload: dict):
    """Explicit deployment/rollback at inference-server level. Governance
    (statuses, who/when) lives in the backend ModelVersion table."""
    from .model_registry import activate_version
    version = (payload or {}).get("version")
    if not version:
        raise HTTPException(status_code=400, detail="version required")
    try:
        meta = activate_version(version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "activated", "active": meta.get("version")}


@app.post("/models/evaluate")
def model_evaluate(payload: dict):
    """Frozen-test evaluation of a registered checkpoint. Records must include
    image_id/image_path/pest_id; only the manifest's frozen test ids are used."""
    from .datasets import load_manifest
    from .evaluation import evaluate_checkpoint
    from .model_registry import version_meta
    version = (payload or {}).get("version")
    dataset_version = payload.get("dataset_version")
    records = payload.get("records") or []
    if not version or not dataset_version:
        raise HTTPException(status_code=400, detail="version and dataset_version required")
    meta = version_meta(version)
    if not meta:
        raise HTTPException(status_code=404, detail="Unknown model version")
    manifest = load_manifest(dataset_version)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Unknown dataset version")
    try:
        report = evaluate_checkpoint(meta, records, manifest,
                                     max_images=payload.get("max_images"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}") from exc
    # Persist next to the artifact for portability between servers.
    try:
        import json as _json
        from pathlib import Path as _P
        p = _P(meta.get("checkpoint_path")).parent / "eval_frozen.json"
        p.write_text(_json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass
    try:
        from .tracking import track_evaluation
        track_evaluation(f"eval-{version}", report,
                         tags={"model_version": version, "dataset_version": dataset_version})
    except Exception:
        pass
    return report


@app.post("/models/compare")
def model_compare(payload: dict):
    from .evaluation import compare_reports
    return compare_reports(payload.get("current"), payload.get("candidate"),
                           important_classes=payload.get("important_classes"))


@app.post("/active-learning/tune")
def active_learning_tune(payload: dict):
    """Propose review-priority weights from labelled review outcomes."""
    from .active_learning import tune_priority_weights
    return tune_priority_weights(payload.get("records") or [])


@app.get("/active-learning/unknown-clusters")
def active_learning_clusters():
    """Visually coherent groups of unidentified crops = candidate new pests."""
    from .active_learning import unknown_clusters
    return unknown_clusters()


@app.post("/datasets/build")
def dataset_build(payload: dict):
    from .datasets import build_dataset
    version = (payload or {}).get("version")
    records = payload.get("records") or []
    if not version or not records:
        raise HTTPException(status_code=400, detail="version and records required")
    try:
        manifest = build_dataset(
            records, version,
            previous_frozen_test_ids=payload.get("previous_frozen_test_ids"),
            annotation_version=payload.get("annotation_version", "v1"),
            test_fraction=float(payload.get("test_fraction", 0.2)),
            dup_threshold=int(payload.get("dup_threshold", 6)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return manifest


@app.get("/datasets")
def dataset_list():
    from .datasets import list_datasets
    return {"datasets": list_datasets()}


@app.get("/datasets/{version}")
def dataset_get(version: str):
    from .datasets import load_manifest
    manifest = load_manifest(version)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Dataset version not found")
    return manifest


@app.get("/models/free-base-models")
def free_base_models():
    return {
        "models": [
            {"id": "mobilenet_v3_small", "name": "MobileNetV3 Small", "license": "TorchVision BSD-style", "best_for": "8-core CPU VPS fast training/inference"},
            {"id": "mobilenet_v3_large", "name": "MobileNetV3 Large", "license": "TorchVision BSD-style", "best_for": "better accuracy with moderate CPU cost"},
            {"id": "resnet18", "name": "ResNet-18", "license": "TorchVision BSD-style", "best_for": "stable baseline from scratch"},
            {"id": "efficientnet_b0", "name": "EfficientNet-B0", "license": "TorchVision BSD-style", "best_for": "accuracy-oriented CPU/GPU training"},
        ],
        "policy": "weights=None is used. The CitriSurksha model is trained from your own verified dataset only. No paid AI/commercial API is used.",
    }


@app.post("/knowledge/items")
def add_knowledge(payload: KnowledgeIn):
    item = payload.model_dump()
    item["id"] = str(uuid.uuid4())
    item["created_at"] = datetime.utcnow().isoformat()
    append_knowledge(item)
    return {"status": "stored", "item": item}


@app.get("/knowledge/items")
def list_knowledge():
    return {"items": read_knowledge(limit=500)}


@app.post("/predict", response_model=Prediction)
def predict(image: UploadFile = File(...)):
    content = image.file.read()
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="Invalid or empty image")
    try:
        img = Image.open(io.BytesIO(content)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Unsupported image file") from exc

    # AI_ENGINE=pipeline opts into the multi-stage pipeline (quality -> YOLO11 ->
    # CNN signal -> decision engine). The legacy single-CNN engine remains the
    # default and the guaranteed fallback until the pipeline is validated.
    try:
        from .pipeline import pipeline_enabled, run_pipeline
        if pipeline_enabled():
            return Prediction(**run_pipeline(content))
    except HTTPException:
        raise
    except Exception:
        if os.getenv("AI_ENGINE", "legacy").strip().lower() == "pipeline":
            raise  # explicit pipeline mode: surface errors, never silently fake
        # legacy mode: pipeline import/runtime problems must not affect service
    return Prediction(**inference_engine.predict(img))


@app.post("/memory/index-verified")
def memory_index_verified(payload: dict):
    """Backend pushes expert-verified images here; embeddings are stored in
    Qdrant with verification metadata. Never stores pest knowledge."""
    from .memory import VisualMemory
    records = payload.get("records") or []
    return VisualMemory().index_verified(records)


@app.get("/memory/stats")
def memory_stats():
    from .memory import VisualMemory
    return VisualMemory().stats()


@app.get("/pipeline/info")
def pipeline_info():
    """Diagnostics for the multi-stage pipeline. No credentials or paths beyond
    the configured YOLO weights name are exposed."""
    from .decision import ThresholdConfig
    from .detector import detector_config
    from .pipeline import pipeline_enabled
    dcfg = detector_config()
    return {
        "engine": "pipeline" if pipeline_enabled() else "legacy",
        "pipeline_version": "pipeline-v1",
        "stages": ["opencv_quality", "yolo11_detector", "legacy_cnn_signal",
                    "dinov2_qdrant_memory", "openclip_signal", "decision_engine"],
        "clip": {
            "enabled": os.getenv("CLIP_ENABLED", "true").strip().lower() == "true",
            "model": os.getenv("CLIP_MODEL", "ViT-B-32"),
            "pretrained": os.getenv("CLIP_PRETRAINED", "openai"),
            "role": "secondary weak signal only",
        },
        "yolo": {k: (os.path.basename(v) if k == "weights" and v else v) for k, v in dcfg.items()},
        "decision_thresholds": ThresholdConfig.load().__dict__,
        "paid_ai_services": False,
    }


@app.post("/train/jobs")
def create_training_job(payload: TrainingRequest):
    ensure_store()
    job_id = str(uuid.uuid4())
    job_path = f"/app/model-store/jobs/{job_id}.json"
    job = {
        "job_id": job_id,
        "status": "running",
        "request": payload.model_dump(),
        "created_at": datetime.utcnow().isoformat(),
        "training_type": "supervised_image_classification_from_scratch",
    }
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)

    for rec in payload.knowledge_records:
        append_knowledge({**rec, "id": str(uuid.uuid4()), "created_at": datetime.utcnow().isoformat()})

    try:
        result = train_classifier(payload.model_dump())
        job["status"] = result.get("status", "completed")
        job["completed_at"] = datetime.utcnow().isoformat()
        job["metrics"] = result.get("metrics", {})
        job["model_version"] = result.get("version")
        job["environment"] = result.get("environment")
        job["artifacts"] = {k: result.get(k) for k in ["checkpoint_path", "torchscript_path", "labels_path"]}
        try:
            from .tracking import track_training_run
            job["mlflow_tracked"] = track_training_run(
                run_name=job_id,
                params={**payload.model_dump(exclude={"training_records", "knowledge_records"}),
                        **(result.get("environment") or {})},
                metrics=result.get("metrics", {}),
                artifacts={"checkpoint": result.get("checkpoint_path"),
                           "torchscript": result.get("torchscript_path")},
                tags={"dataset_version": payload.dataset_version,
                      "architecture": payload.base_model,
                      "model_version": result.get("version") or "none"})
        except Exception:
            job["mlflow_tracked"] = False
    except Exception as exc:
        job["status"] = "failed"
        job["completed_at"] = datetime.utcnow().isoformat()
        job["metrics"] = {"error": str(exc)}

    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)
    return job


@app.get("/train/jobs/{job_id}")
def get_training_job(job_id: str):
    path = f"/app/model-store/jobs/{job_id}.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Job not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/train/yolo")
def create_yolo_training_job(payload: dict):
    """Bootstrap YOLO11 detector training on verified classification images
    (full-image bootstrap boxes). Registers a 'testing' model; deployment still
    requires evaluation + explicit approve/deploy."""
    from .yolo_train import train_yolo
    ensure_store()
    result = train_yolo(payload or {})
    return result
