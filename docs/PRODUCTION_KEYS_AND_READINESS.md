# Production Keys, Credentials and Readiness Checklist

## Training implementation status

The old placeholder in `ai-service/training/train.py` has been replaced. The CLI training script now calls the same real PyTorch/TorchVision training engine used by the AI API:

```text
ai-service/app/ml.py::train_classifier
```

Implemented training features:

- TorchVision model creation with `weights=None`
- CPU-first and GPU-ready device selection
- image preprocessing and augmentation
- train/validation split
- cross entropy training loop
- accuracy, macro F1, per-class precision/recall/F1
- confusion matrix
- checkpoint export `model.pt`
- TorchScript export `model.torchscript.pt`
- labels export `labels.json`
- active model registry update

## Production credentials you must configure

### 1. Backend API secret

Required in backend `.env`:

```env
API_SECRET_KEY=CHANGE_TO_LONG_RANDOM_SECRET
```

Use a 32+ character random value.

### 2. PostgreSQL database

Required:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/citrisurksha
```

If using managed PostgreSQL, also configure firewall/IP allowlist.

### 3. Redis cache

Recommended:

```env
REDIS_URL=redis://127.0.0.1:6379/0
```

If Redis is missing, backend uses in-memory fallback, but production should use Redis.

### 4. Firebase Admin SDK service account

Required for backend push sending:

```text
backend/app/firebase-service-account.json
```

or:

```env
FIREBASE_SERVICE_ACCOUNT_PATH=/secure/path/firebase-service-account.json
```

Never commit this key to public git.

### 5. Firebase mobile config files

Required for mobile builds:

```text
mobile/google-services.json
mobile/GoogleService-Info.plist
```

### 6. iOS APNs key in Firebase

Required for iOS FCM push delivery:

Firebase Console → Project Settings → Cloud Messaging → Apple app configuration → APNs Auth Key

### 7. Expo/EAS environment

Required for mobile builds:

```env
EXPO_PUBLIC_API_URL=https://api.yourdomain.com/api
```

Set this in EAS env or your build shell before building.

### 8. Admin panel build env

Required before building admin panel:

```env
VITE_API_URL=https://api.yourdomain.com/api
```

### 9. SSL/TLS certificates

Use Certbot/Nginx or hosting provider SSL for:

```text
https://api.yourdomain.com
https://admin.yourdomain.com
```

### 10. Optional dataset provider keys

Only needed if you programmatically download external datasets:

- Kaggle API token: `~/.kaggle/kaggle.json`
- Roboflow API key
- Hugging Face token for private/gated datasets

The current system registers dataset sources but does not auto-download huge datasets without your license review.

## Runtime readiness checks

### Backend

```bash
curl https://api.yourdomain.com/api/health
```

### AI service

```bash
curl https://api.yourdomain.com/ai/health
```

### Database

Admin API:

```http
GET /api/admin/system/database
```

### Firebase

Admin panel:

```text
Push Notification → Firebase Status
```

Should show:

```text
Firebase initialized: Yes
Credential found: 1
```

### AI class coverage

Admin panel:

```text
Train AI → Class Coverage
```

For production 20-class model, every pest class should have verified images.

## Important production note

The system is fully wired and functional, but production-grade visual accuracy depends on uploading verified labelled images for all 20 pest classes plus `no-citrus-pest` negative images, then training the PyTorch model.
