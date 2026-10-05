# CitriSurksha Custom PyTorch AI Model

CitriSurksha now uses a custom image classification pipeline built with **Python, PyTorch, TorchVision, FastAPI and PostgreSQL**.

## Principles

- No paid AI service.
- No commercial image-recognition API.
- TorchVision architectures are created with `weights=None`, so the model is trained from CitriSurksha's own verified dataset.
- CPU-first for an 8-core VPS, GPU-ready for future scaling.
- Architecture supports future object detection and disease segmentation modules.

## Model task

Initial model type:

```text
image classification
```

Outputs:

- `is_citrus_pest`
- `pest_id`
- `pest_name`
- `confidence`
- `severity_level`
- `stage`
- `top_k`
- `explanation`
- `recommendation`

If no trained model is registered, inference returns a clear "model not trained yet" response instead of fake predictions.

## Supported free architectures

- `mobilenet_v3_small` - recommended for 8-core CPU VPS
- `mobilenet_v3_large`
- `resnet18`
- `efficientnet_b0`

All are instantiated with `weights=None`.

## Dataset sources

The admin training endpoint automatically collects:

1. Admin uploaded verified labelled pest images.
2. Expert-approved farmer images.
3. Negative/non-pest images labelled as `no-citrus-pest`.
4. Pest catalogue/classes from PostgreSQL.
5. Scientist/developer/browser documentation stored as AI knowledge records.

## Important non-pest handling

To correctly reject unrelated images, collect and label negative images with:

```text
pest_id = no-citrus-pest
```

Examples:

- people
- vehicles
- documents
- non-citrus crops
- random objects
- healthy citrus images if you want a separate healthy class

The inference layer also uses a confidence threshold. If confidence is below threshold, it returns no confirmed citrus pest.

## Training flow

Admin panel -> AI Training:

1. Upload labelled images.
2. Feed scientist/developer/browser documents.
3. Select architecture.
4. Click **Train Custom PyTorch AI**.

Backend sends verified image records and knowledge records to AI service.

AI service:

1. Validates image paths.
2. Builds label mapping.
3. Applies preprocessing and augmentation.
4. Trains the TorchVision classifier on CPU/GPU.
5. Evaluates validation accuracy, macro F1, per-class metrics and confusion matrix.
6. Saves versioned artifacts:
   - `model.pt`
   - `model.torchscript.pt`
   - `labels.json`
   - metrics in active model registry
7. Registers the active model for inference.

## Local run

```bash
cd citrisurksha
cp .env.example .env
docker compose up --build
```

Admin login:

```text
Phone: 9999999999
Password: admin123
```

AI health:

```bash
curl http://localhost:8080/ai/health
```

## Production scaling

- For the 8-core VPS, use `mobilenet_v3_small`, batch size 4-8 and 3-10 epochs.
- Add more verified images per class before increasing model size.
- For GPU, set `FORCE_CPU=false` and run on CUDA-enabled containers.
- Future object detection can be added as another model task using Faster R-CNN/YOLO-style open-source implementations.
- Future disease segmentation can be added with U-Net/DeepLab-style modules.

## Clean architecture modules

AI service modules:

- `model_registry.py` - active model/version registry
- `ml.py` - dataset, augmentation, training, evaluation, export and inference
- `main.py` - FastAPI API layer

Backend modules store users, images, detections, feedback, training images, knowledge feed and training jobs in PostgreSQL.
