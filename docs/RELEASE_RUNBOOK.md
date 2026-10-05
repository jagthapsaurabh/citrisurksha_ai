# CitriSuraksha AI — Release Runbook (upgrade step 12)

The governed path from raw farmer uploads to a safer production model.
Every gate exists so that **no unverified image trains** and **no unevaluated
model deploys**.

## 0. Continuous intake (always on)

1. Farmer scans → pipeline decides (`identified / uncertain / unknown / poor_image /
   no_pest_detected / non_target_image`) and stores full evidence in `detections.ai_response`.
2. Unknown/uncertain crops are embedded into `unknown_pest_candidates` (Qdrant) for
   novel-pest clustering.
3. Admin reviews via **Farmer Uploads**, guided by the **priority review queue**
   (`GET /admin/ai/review-queue`). Verify / Correct / Approve-for-training.
   Approved uploads become **verified** `TrainingImage` rows (authoritative labels).

## 1. Dataset version

4. `POST /admin/ai/datasets {"version":"dataset-vN"}` — immutable manifest with
   frozen test set, dedupe report, split map. Test ids can never leak to training.

## 2. Train

5. Classifier: `POST /admin/ai/train {"dataset_version":"dataset-vN","base_model":...}`
   (trains only on train+val splits; registers status `testing`, never activates).
6. Detector: `POST /admin/ai/train-yolo {"dataset_version":"dataset-vN"}` (bootstrap
   boxes; also status `testing`).
7. Optional MLflow (`MLFLOW_ENABLED=true`) records params/metrics/artifacts.

## 3. Evaluate (frozen test set only)

8. `POST /admin/ai/models/{id}/evaluate` → accuracy, macro P/R/F1, per-class P/R/F1/AP,
   confusion matrix, latency. Stored as `metrics.frozen_eval`.
9. `scripts/latency_report.py` — per-stage budget check (quality/detector/cnn/dino/clip/
   decision/total). Any over-budget stage is a release blocker on that hardware.

## 4. Compare & approve

10. `POST /admin/ai/models/{id}/compare` → recommendation vs current production:
    worse on any important class ⇒ `reject`; small overall regression ⇒ `manual_review`.
11. `POST /admin/ai/models/{id}/status {"status":"approved"}` (human decision).

## 5. Deploy (gated server-side)

12. `POST /admin/ai/models/{id}/deploy` — refused unless `frozen_eval` exists and,
    when a production model exists, `comparison.recommendation == "deploy"`.
    AI service activates the checkpoint; old production archived with rollback trail.

## 6. Monitor & loop

13. Watch: dashboard KPIs, `review_priority` queue depth, unknown-cluster sizes
    (`GET /admin/ai/unknown-clusters`), push delivery logs, `GET /pipeline/info`.
14. Periodically `POST /admin/ai/tune-priority` → review accepted weights into
    `ACTIVE_LEARNING_WEIGHTS`.
15. Any regression in the field: `POST /admin/ai/models/rollback` (one call).

## Security checklist (run before every release)

`python3 scripts/security_check.py` — tracked secrets, 20 MB upload cap, path
traversal, auth enforcement on admin/farmer APIs, AI diagnostics leak check.
Non-zero exit blocks the release.
