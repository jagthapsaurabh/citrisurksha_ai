# AI Training Plan for 1M+ Citrus Pest Images

## Goal

Train an image model that detects citrus pests/insects and optionally lifecycle stage/damage severity.

Recommended outputs:

1. Pest class: psyllid, leaf miner, aphid, whitefly, mites, scales, fruit fly, healthy/unknown, etc.
2. Lifecycle stage: egg, larva/nymph, pupa, adult, damage-only.
3. Severity: low, medium, high.
4. Confidence and top-k classes.

## Dataset strategy

- Store all images in S3/MinIO: `s3://citrisurksha-images/{raw,training,validation}`.
- Metadata table fields: image URI, pest label, lifecycle stage, crop variety, region, date, source, expert reviewer, quality score.
- Split by farm/date to avoid leakage, not random image-only split.
- Keep farmer images unverified until admin/expert approval.
- Deduplicate using perceptual hash and SHA-256.

## Model approach

- Start with transfer learning: ConvNeXt Tiny/Base, EfficientNetV2, Swin Transformer, MobileNetV3 for edge/offline.
- Use image augmentations: resize/crop, brightness/contrast, blur, rotation, cutmix/mixup.
- Use class balancing or focal loss for rare pests/stages.
- Export final model to ONNX/TorchScript for efficient inference.

## Training pipeline

1. Admin uploads labelled images and pest details.
2. Farmer detection images enter review queue.
3. Expert approves/corrects label and lifecycle stage.
4. Backend creates dataset version manifest.
5. GPU worker trains model using manifest.
6. Evaluate on holdout set:
   - top-1 accuracy
   - macro F1
   - per-class recall
   - lifecycle stage accuracy
   - confusion matrix
7. If metrics pass gate, register model.
8. Deploy canary to AI inference service.
9. Monitor real-world low-confidence rate and expert corrections.

## Continuous learning

- Never automatically train from unverified farmer uploads.
- Prioritize low-confidence and high-impact pest images for review.
- Maintain model rollback.
- Keep a fixed golden test set that never enters training.

## Feeding data to AI from admin

Implemented scaffold endpoints:

- `POST /api/admin/training-images`: upload verified labelled image.
- `POST /api/admin/detections/{id}/approve-training`: promote farmer image after expert review.
- `POST /api/admin/ai/train`: queue a training job.

## Replacing mock AI

Current AI service uses deterministic mock classification for app integration testing. Replace `ai-service/app/main.py` predict function with:

1. Load active model checkpoint from model registry.
2. Preprocess image identically to training.
3. Run inference.
4. Return pest_id, pest_name, lifecycle stage, confidence and top-k.

Do not run training inside the inference API process in production.

## Implemented custom PyTorch classifier

The AI service now includes a functional PyTorch/TorchVision classifier training pipeline in `ai-service/app/ml.py`.

Key implementation details:

- TorchVision architectures are instantiated with `weights=None`.
- CPU-first defaults: `FORCE_CPU=true`, `TORCH_NUM_THREADS=8`.
- Dataset records are collected from verified admin images and expert-approved farmer images.
- Image preprocessing includes resize, crop, rotation, flip and color jitter augmentations.
- Training exports:
  - PyTorch checkpoint `model.pt`
  - TorchScript export `model.torchscript.pt`
  - label map `labels.json`
  - active model metadata and metrics
- Validation metrics include accuracy, macro F1, per-class precision/recall/F1 and confusion matrix.
- Non-pest rejection is supported through the `no-citrus-pest` negative class plus confidence thresholding.

For a reliable production model, collect at least 100+ verified images per pest/stage and include negative/non-pest examples.
