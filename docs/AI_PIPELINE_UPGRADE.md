# CitriSuraksha AI — Multi-Stage Vision Pipeline Upgrade

Status: **Steps 1–12 complete — full target pipeline implemented and validated** (audit, OpenCV + YOLO11, validation harness, DINOv2 + Qdrant visual memory, OpenCLIP secondary signal, calibration format + evidence/audit trail, dataset versioning + governed model registry, frozen-test evaluation + comparison-gated deploys, optional MLflow + bootstrap YOLO training, admin governance UI, active learning, production validation pack).
Steps 9–12 (MLflow wrapper, admin upgrades, active learning) follow in the same incremental style.

## Target architecture

```
Farmer image
  -> OpenCV quality gate            (app/quality.py)
  -> YOLO11 detector / fallback     (app/detector.py)
  -> crop detected insect
  -> signals: YOLO class votes, legacy CNN, (later DINOv2+Qdrant, OpenCLIP)
  -> Decision Engine                (app/decision.py)
  -> identified | uncertain | unknown | poor_image | no_pest_detected | non_target_image
  -> PostgreSQL pest dossier joined by backend (knowledge stays in Postgres)
```

Training loop (existing verification rules preserved, never auto-train on raw uploads):

```
farmer upload -> prediction -> farmer feedback -> expert verification
 -> verified label -> dataset version -> YOLO/CNN training -> evaluation
 -> (MLflow) -> model registry -> admin approval -> production -> rollback-ready
```

## Step 1 audit results

- Legacy engine: `ai-service/app/ml.py` (`InferenceEngine`, `train_classifier`, bootstrap mode), JSON-file registry `model_registry.py` (single active file, no history/rollback).
- Backend proxies: `routers/detections.py` (`prepare_ai_image` 1024px/q82, sha-cache, stores full AI JSON in `detections.ai_response`), `routers/admin.py` (`/ai/train`, `/ai/class-coverage`, approve-for-training), `routers/training.py` (farmer submissions unverified by design).
- Duplicates consolidated later: pest knowledge exists in backend `AiKnowledgeItem`, ai-service `knowledge.jsonl` and seed modules. **Qdrant will store embeddings only, never knowledge.**
- Reused as-is: `DEFAULT_CLASSES`, `register_model/active_model`, upload helpers, cache, review endpoints, `Prediction` schema (extended additively).

## Step 2 — what changed

New modules (ai-service):
- `app/quality.py` — OpenCV quality gate: corrupt-file decode, resolution, brightness, contrast, blur (Laplacian), texture (Canny), plant/pest scene check. Poor images become `poor_image`/`non_target_image`, never a fake prediction. All thresholds env-configurable.
- `app/detector.py` — YOLO11 wrapper (model/imgsz/conf/iou/device/batch configurable, model cached once, tiled inference ONLY above `DETECTOR_TILE_TRIGGER`), crop generation with padding + centre-crop fallback, honest `opencv_fallback` localiser while no trained pest-YOLO weights exist.
- `app/decision.py` — pure decision engine: weighted evidence fusion, cross-source disagreement => `uncertain`, margins, negative class, weak-signal protection (bootstrap can guide, never confirm), `review_priority` (active-learning seed). Thresholds re-read from env per call, calibratable later.
- `app/pipeline.py` — orchestrator; output is **additive** to the existing mobile contract (`decision`, `candidates`, `evidence`, `quality`, `detector`, `review_priority`, `timings`); old clients unaffected.
- `app/main.py` — `AI_ENGINE=legacy|pipeline` feature flag (legacy stays the default and guaranteed fallback; explicit pipeline mode surfaces errors instead of silently faking), new `/pipeline/info` diagnostics (no secrets).
- `app/schemas.py` — `Prediction` extended with optional pipeline fields only.

Dependencies added (`ai-service/requirements.txt`):
`opencv-python-headless==5.0.0.93`, `ultralytics==8.4.173`, `ultralytics-thop==2.2.2`.
(GUI `opencv-python` deliberately excluded — no libGL on servers.)

Environment variables added (see `.env.example` / `.env.nodocker.example`):
`AI_ENGINE, YOLO_WEIGHTS, YOLO_MODEL, YOLO_IMGSZ, YOLO_CONF, YOLO_IOU, YOLO_DEVICE, YOLO_BATCH,
DETECTOR_TILING, DETECTOR_TILE_TRIGGER, DECIDE_IDENTIFY_MIN, DECIDE_MARGIN_MIN,
DECIDE_NEGATIVE_MIN, DECIDE_SUPPORT_MIN, W_YOLO, W_CNN, W_DINO, W_CLIP`.

Database migration: **none required** (pipeline output rides inside `detections.ai_response` JSON).
Future steps will add nullable `detections.decision/review_priority` plus `DatasetVersion`/`ModelVersion` tables with SQLite/Postgres migration scripts.

## Step 3 — validation harness

`scripts/compare_engines.py` runs legacy and pipeline over the same images and writes
`scripts/compare_report.json` (agreement rate, decision counts, per-stage latency).
First run on 4 real citrus photos: agreement 1.0, pipeline avg 0.019 s CPU, all four
decisions `uncertain` with `review_priority` ~0.87 — correct honesty for an untrained
system (nothing is labelled "confirmed").

Tests: `ai-service/tests/test_pipeline_step2.py` — **18 passed** covering quality gate
(blank/dark/tiny/corrupt/natural), fallback detector boxes + crops + tiling trigger,
decision rules (poor_image, non_target, no_pest, the spec's disagreement example =>
uncertain, agreement => identified, weak-only never identified, small margin =>
uncertain, review priority ordering) and API compatibility in both engine modes.

## Current limitations (honest)

- No trained YOLO11 pest weights yet: detector runs in labelled `opencv_fallback` mode;
  class-level detection currently relies on the legacy CNN signal (bootstrap until trained).
- DINOv2/Qdrant/OpenCLIP not wired yet (steps 4–6); decision engine already accepts them as signals.
- Model registry still JSON-file based; DB-backed `ModelVersion`/`DatasetVersion` + MLflow come in steps 7–9.
- Thresholds are sensible defaults, not yet calibrated from validation data.

## Step 4 — what changed (DINOv2 + Qdrant visual memory)

New modules (ai-service):
- `app/embeddings.py` — pretrained DINOv2 ViT-S/14 (open Meta research weights via torch.hub,
  cached locally; `DINOV2_ENABLED` kill-switch; cached model; 384-d unit-norm embeddings;
  `EMBEDDING_VERSION=dinov2-vits14-v1`). Embedder is similarity-only, never a detector.
- `app/memory.py` — Qdrant visual memory. Embedded local mode by default
  (`QDRANT_PATH`, default `<model-store>/qdrant`), optional self-hosted server via
  `QDRANT_URL`/`QDRANT_API_KEY`. Payload per spec: image_id, pest_id, pest_class, stage,
  dataset_version, verification_status, source, embedding_version. `query()` returns top
  matches, per-pest aggregation, support ids, top-1/top-2 score and margin. Cached client
  (one per backend target). Knowledge stays in PostgreSQL — Qdrant stores embeddings only.
- Pipeline wiring (conditional execution): DINOv2+Qdrant runs only when quality is
  acceptable AND locality evidence exists; similarity ≥ `DINO_MIN_SIM` becomes a
  `dino_qdrant` signal (weak below `DECIDE_SUPPORT_MIN` support); visually novel crops add
  a weak negative vote. Output gains additive `memory` + `dino_qdrant` timing fields.
- `app/main.py` — `POST /memory/index-verified`, `GET /memory/stats`.
- Backend `admin.py` — verified images are pushed to the memory fire-and-forget on
  `verify` and `approve-for-training`; new bulk `POST /admin/ai/reindex-memory`.
- `app/decision.py` — fusion now normalises per pest by the weight of sources that voted
  for it (one strong verified-memory match is no longer diluted by weak signals).

Dependencies added: `qdrant-client==1.19.1`.
Environment variables added: `DINOV2_ENABLED, DINO_HUB_DIR, QDRANT_PATH, QDRANT_URL,
QDRANT_API_KEY, MEMORY_ENABLED, MEMORY_TOP_K, DINO_MIN_SIM` (both `.env` examples).
Database migration: **none**.

Validation:
- Unit/integration: 26/26 tests pass (aggregation top1/top2/margin/support, deterministic
  UUIDv5 point ids, missing-path handling, disabled/unavailable degradation, stats,
  pipeline signal consumption, novelty negative vote, memory endpoints).
- Real-weights smoke (`scripts/smoke_dino_qdrant.py`): SMOKE_OK — 384-d embeddings,
  direct query similarity 1.0 with support ids, pipeline crop query 0.681 → `identified`
  with verified-memory evidence.

Current limitations: index population happens on review events + manual reindex; automatic
re-index on embedding-version bump is not implemented yet; OpenCLIP signal still absent.

## Step 5 — what changed (OpenCLIP secondary signal)

- `ai-service/app/clip_signal.py` (new) — OpenCLIP ViT-B-32 with open "openai" weights
  (open source, no paid API). Configurable per-pest text prompts: bundled override file
  `ai-service/config/clip_prompts.json` used by default, replaceable via `CLIP_PROMPTS_FILE`;
  template prompts for all 20 pests + dedicated negative prompts for `no-citrus-pest`.
  Per-class text features are averaged over prompts and cached; model cached once.
- Pipeline wiring: CLIP runs only under the same locality gate; its vote is ALWAYS
  `weak` — it can support or contradict, never decide. Fusion now ranks weak-only
  candidates half as high, so a strong verified-memory/YOLO agreement can never be
  out-ranked by zero-shot CLIP alone.
- `app/main.py` — `/pipeline/info` exposes CLIP stage + configured model and its role.
- Dependencies added: `open_clip_torch==3.3.0`.
- Environment variables added: `CLIP_ENABLED, CLIP_MODEL, CLIP_PRETRAINED, CLIP_PROMPTS_FILE`.
- Database migration: none.

Validation:
- 32/32 tests pass, including step-5 rules: prompt coverage + override file, disabled/
  failed-load degradation, **CLIP-alone can never identify**, weak-vs-strong ranking,
  strong cross-source contradiction => uncertain.
- Real-weights smoke (`scripts/smoke_clip.py`): SMOKE_CLIP_OK, ~0.1 s/image after warm-up.
  Zero-shot top-3 on fine-grained citrus pests is visibly unreliable (orchard photo scored
  "California red scale") — empirical confirmation of the weak-signal design rule.

Current limitations: CLIP prompts not yet tuned/calibrated; training-side upgrades
(dataset/model versioning, MLflow, admin studio) remain steps 7–10.

## Step 6 — what changed (calibration format + evidence/audit trail)

- `ai-service/app/calibration.py` (new) — canonical calibration record schema
  (`record_version`, expert-review label, full feature snapshot: quality, signals per
  source, memory top-1/top-2/margin/support, clip, cnn, fused, decision), `validate_record`,
  and `suggest_thresholds()` which proposes `W_*` weights from per-source separability
  (mean score when the source agrees with the expert label vs when it does not) and
  `DECIDE_IDENTIFY_MIN` / `DECIDE_MARGIN_MIN` from fused-score/margin distributions of
  correct vs wrong predictions. **`applied` is always False** - proposals are written to
  JSON for human review; defaults are blended 50/50 until >=100 usable records exist.
- `backend/app/calibration.py` (new) — builds labelled records from expert-reviewed
  detections only (never raw farmer uploads), re-using the evidence snapshot already
  persisted in `detections.ai_response` at prediction time.
- `backend/app/routers/admin.py` — `GET /admin/ai/calibration-export` (admin-only).
- `scripts/calibrate_decision.py` — export -> proposal CLI
  (`scripts/decision_config_proposal.json` output).

Dependencies added: none. Environment variables added: none (proposals map onto the
existing `DECIDE_*` / `W_*` variables after human review). Database migration: none.

Validation:
- ai-service 36/36 + backend 3/3 tests pass (schema validation, separability weights
  W_DINO > W_CLIP on synthetic separable data, no-data keeps defaults, poor-quality
  records excluded, reviewed-only export, legacy-response tolerance).
- CLI exercised end-to-end on a synthetic 15-record export: sep_dino_qdrant 0.45 vs
  sep_clip -0.3, identify-min proposed 0.6, `applied: false`.

Current limitations: proposals need a frozen-test re-evaluation before being adopted
(arrives with steps 7-8); admin UI for the evidence trail still to come (step 10).

## Step 7 — what changed (dataset versioning + governed model registry)

Dataset versioning (`ai-service/app/datasets.py`, new):
- Immutable manifests at `<model-store>/datasets/<version>.json` with image count,
  class distribution, train/val/test counts, source splits, annotation version,
  creation time and dups removed.
- **Frozen test set**: created stratified on first version, inherited by all later
  versions; train/val splits can never contain frozen test ids (leakage-proof).
- **Near-duplicate detection**: 64-bit dHash, hamming <= 6 inside a class collapses
  duplicates (first kept, counted), so duplicates cannot sit in two splits.
- Endpoints: `POST /datasets/build`, `GET /datasets`, `GET /datasets/{version}`.
- Backend: `DatasetVersion` table; `POST /admin/ai/datasets` (immutable, one version
  name once), `GET /admin/ai/datasets`. `POST /admin/ai/train` now filters training
  records to the manifest's train+val ids when a dataset version is supplied.

Model registry (`ai-service/app/model_registry.py` upgraded):
- `register_model(..., activate=False)` default: versions/ history always grows, the
  ACTIVE production pointer only moves via explicit `activate_version()` (validates
  checkpoint exists). `AUTO_ACTIVATE_TRAINING=true` is the opt-in escape hatch.
- `train_classifier` now registers with status `testing` and returns environment info
  (python/torch/cuda/gpu/code version); `GET /models/versions`, `POST /models/activate`.
- Corrupt-checkpoint guard: legacy engine degrades to bootstrap instead of crashing.

Governance (`backend/app/model_governance.py` + `ModelVersion` table, new):
- Statuses training/testing/approved/production/rejected/archived with an explicit
  transition map; `production` reachable only via deploy/rollback.
- `deploy_model` refuses models without evaluation metrics (no blind deploys), calls
  AI activate, demotes the old production to archived with `was_production=True`.
- `rollback_model` redeploys the most recent previous production (or an explicit id).
- Admin endpoints: `GET /admin/ai/models` (DB rows + live active pointer),
  `POST /admin/ai/models/{id}/status`, `.../deploy`, `POST /admin/ai/models/rollback`.
- New tables are created by `create_all` on existing databases; **no ALTER of existing
  tables**, so SQLite and Postgres upgrades are migration-free for this step.

Environment variables added: `AUTO_ACTIVATE_TRAINING` (default false).

Validation: ai-service 40/40, backend 7/7 tests pass — frozen-test inheritance and
leakage checks, dHash dedupe, register-without-activate, activate-requires-checkpoint,
illegal transitions rejected, deploy-without-metrics rejected, demotion + rollback,
endpoint shape with the AI service down.

Current limitations: frozen-test evaluation metrics for new models (precision/recall/F1/
mAP, per-class, latency) land in step 8/13; admin UI for datasets/model governance in
step 10; MLflow optional wrapper in step 9.

## Step 8 — what changed (frozen-test evaluation + comparison-gated deploys)

- `ai-service/app/evaluation.py` (new):
  - `compute_classification_metrics`: accuracy, macro precision/recall/F1, per-class
    P/R/F1, per-class AP (softmax, one-vs-rest), confusion matrix, and explicit
    `detection_map50` / `detection_map50_95` fields that stay honestly `null` until a
    trained YOLO detector with bounding boxes is evaluated (IoU-based mAP belongs to
    the detector stage; classification quality uses probability-based AP).
  - `evaluate_checkpoint`: runs a registered checkpoint ONLY over the manifest's frozen
    test ids (records supplied by backend), with warm-up and per-image latency.
    Report persisted beside the artifact as `eval_frozen.json` (portable between servers).
  - `compare_reports`: recommendation `deploy | manual_review | reject` — a candidate
    that is better overall but worse on any important class (recall drop > COMPARE_MAX_DROP)
    is REJECTED; small overall regressions go to manual review.
  - Endpoints `POST /models/evaluate`, `POST /models/compare`.
- Backend governance hardening: `deploy_model` now refuses deployment unless the row
  carries `metrics.frozen_eval.frozen_test`, and when a production model exists it also
  requires `metrics.comparison.recommendation == "deploy"`. Rollback keeps its safety
  valve (`require_comparison=False`) since the target was already a validated production
  model. New admin endpoints: `POST /admin/ai/models/{id}/evaluate` and `.../compare`
  (assemble verified records + dataset row, call AI, store report on the model row).

Environment variables added: `COMPARE_MAX_DROP` (0.05), `COMPARE_EPS` (0.01).
Dependencies added: none (scikit-learn already present). Database migration: none
(evaluation reports live inside the existing `model_versions.metrics` JSON).

Validation: ai-service 44/44 and backend 8/8 tests pass, including a REAL end-to-end
pass (train resnet-18 on a 3-class dataset version -> frozen-test evaluation -> 100%
on the never-trained-on test ids, latency reported) and gate tests (deploy without
frozen_eval refused; comparison reject/manual_review refused; rollback still works).
Also fixed a test-hygiene bug this surfaced: scratch MODEL_STORE dirs now live on the
root filesystem, not /tmp tmpfs.

Current limitations: detector-side mAP50/50-95 populate once YOLO training with boxes
exists (bootstrap annotations tooling is the natural next addition); MLflow wrapper in
step 9; admin UI for datasets/evaluation in step 10.

## Step 9 — what changed (optional MLflow + bootstrap YOLO detector training)

- `ai-service/app/tracking.py` (new) — optional MLflow wrapper (`MLFLOW_ENABLED`,
  `MLFLOW_TRACKING_URI`, `MLFLOW_EXPERIMENT`). Tracks training runs (params, numeric
  metrics, checkpoint artifacts, dataset/architecture tags) and frozen evaluations.
  Every call is a no-op when disabled/uninstalled/unreachable; failures only warn.
  `ai-service/requirements-mlflow.txt` pins `mlflow==3.16.1` as an OPTIONAL extra -
  main requirements unchanged, inference never depends on it.
- `ai-service/app/yolo_train.py` (new) — bootstrap YOLO11 detection dataset builder:
  verified classification images become ultralytics datasets (`images/<split>`,
  `labels/<split>` with full-image boxes `idx 0.5 0.5 1 1`, dataset.yaml with class
  names and an explicit bootstrap-labels comment). Frozen test split kept separate.
  `train_yolo()` trains YOLO11s, copies `best.pt` into the versioned registry with
  `architecture="yolo11s"`, status `testing`, **never activates**.
- Endpoints: `POST /train/yolo` (AI), `POST /admin/ai/train-yolo` (backend; sends
  verified records + manifest splits, stores the ModelVersion row).
- `app/detector.py` — when `YOLO_WEIGHTS` is unset, the detector now adopts a
  **deployed** YOLO detector from the governed registry (active model with
  `yolo*` architecture); otherwise the OpenCV fallback remains.
- `scripts/bootstrap_yolo_annotations.py` — CLI to build the YOLO dataset from
  per-class folders, optionally honouring a dataset manifest's splits.

Environment variables added: `MLFLOW_ENABLED`, `MLFLOW_TRACKING_URI`, `MLFLOW_EXPERIMENT`.
Dependencies added: none mandatory (optional `requirements-mlflow.txt`).
Database migration: none.

Validation: ai-service 49/49 and backend 8/8 tests pass - YOLO dataset splits/label
format/yaml, detector adoption of a deployed YOLO registry model (and refusal for
non-YOLO actives), MLflow real tracking against a sqlite store + disabled no-op,
`/train/yolo` needs-more-data guard.

Current limitations: bootstrap boxes are full-image (localisation quality arrives with
expert boxes); real YOLO training run not executed here (no verified images yet).
Steps 10-12 remain: admin studio UI for datasets/evals/models, active learning queue.

## Step 10 — what changed (admin panel upgrades)

- `admin-panel/src/screens/AIModels.tsx` rewritten as **AI Model Governance**:
  active/production panel with one-click **Rollback**; model table with status chips,
  dataset link, val metrics, frozen-eval badge and comparison verdict; per-row actions
  **Evaluate (frozen test) / Compare vs production / Approve / Reject / Deploy / Details**
  (deploy is server-side gated on frozen eval + comparison=deploy).
  **Dataset Versions** panel (list + immutable build from verified images) and
  **YOLO11 bootstrap detector training** panel.
- `admin-panel/src/screens/FarmerUploads.tsx`:
  **Priority review queue** (active learning) listing unreviewed scans ordered by the
  pipeline's `review_priority`, and an **AI evidence panel** per detection showing
  decision, quality, per-source signals, DINOv2+Qdrant memory (top1/similarity/support/
  margin) and OpenCLIP score.
- Backend `GET /admin/ai/review-queue` (priority-sorted unreviewed detections).
- `admin-panel/src/api.ts`: new governance calls (datasets, evaluate, compare, status,
  deploy, rollback, train-yolo, review-queue). `src/vite-env.d.ts` added.

Validation: admin `vite build` clean; targeted `tsc --strict` over the edited screens
clean; backend 8/8 tests pass.

## Step 11 — what changed (active-learning loop closure)

- `ai-service/app/active_learning.py` (new):
  - **Priority tuning from review outcomes**: calibration records (evidence + expert
    label) tell us when the AI was wrong; per-signal lift `P(wrong|signal)-P(wrong)`
    over low_conf / small_margin / disagreement / weak_support / novel_image /
    clip_conflict produces a proposed weight vector (`POST /active-learning/tune`).
    Proposals only; a human copies accepted weights into `ACTIVE_LEARNING_WEIGHTS`,
    which `decision.review_priority` then uses as an additive boost.
  - **Unknown-image clustering**: crops the pipeline cannot identify are stored as
    DINOv2 embeddings in a dedicated Qdrant collection (`unknown_pest_candidates`);
    greedy leader clustering (`CLUSTER_SIM`, `CLUSTER_MIN`) surfaces coherent groups
    as **candidate new pest classes** (`GET /active-learning/unknown-clusters`).
- `app/pipeline.py` stores an unknown crop embedding (image sha + top candidate)
  whenever the decision is unknown/uncertain.
- Backend: `GET /admin/ai/unknown-clusters`, `POST /admin/ai/tune-priority`
  (auto-builds the calibration export from reviewed detections).
- Admin UI (AIModels): unknown-cluster panel with "CANDIDATE NEW CLASS" badges and a
  "tune priority weights" action; Farmer Uploads keeps the priority review queue.

Environment variables added: `CLUSTER_SIM`, `CLUSTER_MIN`, `ACTIVE_LEARNING_WEIGHTS`.
Dependencies added: none. Database migration: none.

Validation: ai-service 53/53, backend 8/8, admin `vite build` + strict `tsc` over edited
screens clean. Tests cover lift-based tuning (correlated signal wins, too-little-data
guard), signal extraction, cluster recovery (3+3+1 vectors -> two candidate clusters +
singleton), and pipeline->store wiring.

## Step 12 — what changed (production validation pack)

- `ai-service/app/perf.py` (new) — per-stage latency budgets (`BUDGET_<STAGE>`,
  `LATENCY_TOTAL_BUDGET_S` env-overridable) and `check_budget()`; skipped stages never
  fail, over-budget stages do.
- `scripts/latency_report.py` — warm-up + steady-state per-stage report over sample
  images → `scripts/latency_report.json`; current run: **all within budget** (totals
  0.004–0.04 s steady state on CPU; first-call loads excluded by warm-up).
- `scripts/security_check.py` — runnable checklist, **7/7 PASS**: no tracked Firebase
  admin/service-account files; no real `.env` tracked (templates allowed); 20 MB upload
  cap enforced; path traversal blocked; admin & farmer APIs return 401 unauthenticated;
  `/pipeline/info` leaks no credentials or internal paths. Non-zero exit blocks release.
  Wired into the test suites (backend runs it as a test).
- `docs/RELEASE_RUNBOOK.md` — the governed release path: intake → review queue →
  dataset version → train (classifier + YOLO) → frozen evaluation → compare → approve →
  gated deploy → monitor → rollback, with exact endpoints and the security gate.

Environment variables added: `BUDGET_*` stage budgets, `LATENCY_TOTAL_BUDGET_S`.
Dependencies added: none. Database migration: none.

Validation: ai-service 56/56, backend 9/9 (incl. security checklist test), compileall
clean; latency report `OVER-BUDGET FILES: none`; admin build/tsc validated in step 10/11
rounds and unchanged since.

## Programme summary

All twelve steps delivered: honest multi-stage detection (quality → YOLO11 → CNN →
DINOv2+Qdrant → OpenCLIP → decision engine with `I don't know`), governed datasets with
frozen test sets, evaluation-gated deploy/rollback, optional MLflow, bootstrap detector
training, active learning, latency + security validation, and a release runbook.
