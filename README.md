# CitriSurksha

CitriSurksha is a scalable citrus pest/insect detection platform for farmers. It includes:

- **Mobile app**: splash, login, registration, farmer dashboard, pest detection by camera/gallery, detection history, pest management, yearly calendar, blog, profile, notifications.
- **Admin panel**: pest catalogue management, upload pest images/details, review farmer images, manage training data, trigger AI training, publish blogs, manage users and detections.
- **Backend API**: authentication, pest data, detections, history, admin workflows, blog/calendar content, Redis caching, object-storage ready image uploads.
- **AI service**: image inference endpoint, model registry, dataset ingestion, training job skeleton for 1M+ images and active learning from admin/farmer uploads.
- **Infrastructure**: NGINX load balancer, Postgres, Redis cache, MinIO-compatible storage, Docker Compose for local/dev deployment.

> This repository is a production-ready starter scaffold. The AI endpoints run with a safe mock classifier until you train and register a real model checkpoint.

## Suggested stack

| Layer | Technology |
|---|---|
| Mobile | Expo React Native + TypeScript |
| Admin | React + Vite + TypeScript |
| API | FastAPI + SQLAlchemy + Postgres |
| Cache | Redis |
| Object storage | S3/MinIO |
| AI inference/training | FastAPI + PyTorch/TorchVision |
| Load balancer | NGINX |
| Deployment target | Kubernetes/ECS/VM cluster after Docker Compose dev |

## Quick start - local development

```bash
cd citrisurksha
cp .env.example .env
# Build and run core services
docker compose up --build
```

Services:

- API through load balancer: `http://localhost:8080/api`
- AI health: `http://localhost:8080/ai/health`
- Admin dev app source: `admin-panel/`
- Mobile Expo source: `mobile/`
- MinIO console: `http://localhost:9001`

## High-level workflow

1. Farmer logs in or registers in the mobile app.
2. Farmer captures/uploads citrus plant/pest image.
3. Mobile app posts image to `POST /api/detections`.
4. Backend stores the original image, calls AI service `/predict`, enriches response from pest catalogue, caches common pest details, and stores detection history.
5. Farmer receives pest name, lifecycle/stage, confidence, symptoms, prevention, cure, chemical/organic options, and safety instructions.
6. Admin reviews detections and can promote farmer-uploaded images into training data.
7. Admin uploads verified images/details for pests and starts training jobs.
8. AI service trains/evaluates a new model, registers it after accuracy/QA checks, and inference pods hot-load the active model.

## Main API examples

### Farmer detection

```bash
curl -F "image=@leaf.jpg" -F "source=camera" \
  -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/detections
```

### Admin upload labelled pest training image

```bash
curl -F "image=@citrus_psyllid.jpg" -F "pest_id=citrus-psyllid" \
  -F "stage=adult" -F "verified=true" \
  -H "Authorization: Bearer <admin-token>" \
  http://localhost:8080/api/admin/training-images
```

### Start AI training

```bash
curl -X POST -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"dataset_version":"2026-06-30","base_model":"convnext_tiny","epochs":30}' \
  http://localhost:8080/api/admin/ai/train
```

## Important production notes

- For 1M+ images, keep images in S3/MinIO and store labels/metadata in Postgres. Do not put images in DB.
- Use human-in-the-loop approval for farmer images before training.
- Deploy AI inference separately from training workers; inference should be autoscaled on CPU/GPU utilization.
- Use Redis for pest catalogue, blog, calendar and repeated prediction-cache keys.
- Use a model registry with canary deployment and rollback.
- Add pesticide-regulation checks per region before recommending chemicals.

See `docs/ARCHITECTURE.md`, `docs/API.md`, and `docs/AI_TRAINING.md` for implementation details.

## Latest mobile additions

- Added native config folders:
  - `mobile/android/app/src/main/AndroidManifest.xml`
  - `mobile/ios/CitriSurksha/Info.plist`
- Added Android permissions for camera, gallery/images, notifications, internet and network state.
- Added iOS usage descriptions for camera, photo library and notifications.
- Added runtime permission prompts for camera/gallery and notifications.
- Added a mobile **Train AI** tab where farmers can submit labelled pest/lifecycle images for admin review.
- Added admin review endpoints for mobile AI training submissions.

See `mobile/NATIVE_PERMISSIONS.md` for native permission details.

## Expo SDK 54 mobile upgrade

The mobile project has been upgraded to **Expo SDK 54** with generated native folders:

- `mobile/android`
- `mobile/ios`

Key versions:

- Expo `~54.0.35`
- React `19.1.0`
- React Native `0.81.5`
- expo-image-picker `~17.0.11`
- expo-notifications `~0.32.17`

Run mobile checks:

```bash
cd mobile
npm install
npx tsc --noEmit
npx expo-doctor
```

`expo-doctor` may show one expected warning because this project intentionally commits native folders plus Expo prebuild configuration.

## Fix for `java.io.IOException: Failed to download remote update`

The mobile config now disables remote OTA update checks during development:

```json
"updates": {
  "enabled": false,
  "checkAutomatically": "NEVER",
  "fallbackToCacheTimeout": 0
}
```

Use tunnel mode when testing on a physical device:

```bash
cd mobile
npm run start:tunnel
```

See `mobile/TROUBLESHOOTING_REMOTE_UPDATE.md`.

## Mobile UX update

- Bottom footer navbar now has exactly four tabs: **Home**, **Scan**, **Pest Management**, **Profile**.
- Dashboard has responsive square cards for Scan, History, Pest Guide, Year Calendar, Blog, Profile, About App and Terms.
- Dashboard cards are clickable and navigate to their screens.
- Train AI is removed from farmer mobile UI; AI training is admin/agronomist-only from the admin panel.
- All mobile screens use Safe Area handling to avoid content being cut on notches and small devices.
- Profile now supports editable farmer/farm details: acres of land, plants/crops, citrus varieties, irrigation, village/district/state and experience.

## Admin + DB update

- Blog, pest management, year calendar and detection history data are loaded from backend database.
- Admin can view farmer uploaded detection images, see AI result/top-k predictions, and correct wrong pest result/stage/confidence.
- Corrected admin results are visible in the farmer's history/full result screen.
- Admin can update calendar month content from the admin panel.
- Admin AI training now includes free/open-source base model selection: MobileNetV3, EfficientNet-B0, ConvNeXt Tiny and ResNet-50.


## Custom PyTorch AI model

The AI service now uses a custom PyTorch/TorchVision image classification pipeline trained from CitriSurksha's own verified dataset. No paid AI service or commercial image-recognition API is used.

Training data comes from:

- admin uploaded labelled images
- expert-approved farmer images
- negative/non-pest images labelled `no-citrus-pest`
- scientist/developer/browser documentation stored as AI knowledge records
- pest catalogue/classes from PostgreSQL

CPU-first training is configured for an 8-core VPS with GPU-ready code for future scaling. See `docs/PYTORCH_AI.md`.

## Admin panel route-based restructuring

The admin panel is now route-based with separate screen files instead of one large `App.tsx`.

Admin routes:

- `/` Dashboard overview
- `/users` User management / platform users
- `/farmers` Farmer profiles
- `/register-insecticide` Register pest/insect in software and show in app
- `/pest-management` Pest image/details/prevention/cure management
- `/farmer-uploads` Farmer uploaded images, AI result correction, approve for training
- `/blogs` Blog CRUD with HTML/text/image/document support
- `/train-ai` Custom PyTorch AI training and developer/browser/scientist data feed
- `/events` Create farmer events and notification intent
- `/chat` Farmer chat support/escalations
- `/settings` Reset password, theme change, logout

Mobile dashboard now also includes Events and Farmer Chat screens. Events are loaded from database and farmer chat messages are visible in admin.

## Mobile multilingual support

The mobile app now supports three languages:

- English (`en`) - default
- Marathi (`mr`)
- Hindi (`hi`)

Farmers can change language from **Profile → Language**. The selected language updates app labels, dashboard menu, scan/result labels, history/detail labels, pest-management labels, event tab labels and farmer chat labels. Known seeded pest recommendations are localized for Marathi/Hindi with English fallback for admin-created content. Blogs can be filtered by language through the existing blog language field.

## Pest data in all three languages

Pest/insect management now supports English, Marathi and Hindi from the database.

Backend `pests` table includes a `translations` JSON field, for example:

```json
{
  "mr": { "common_name": "...", "symptoms": "...", "prevention": "...", "cure": "..." },
  "hi": { "common_name": "...", "symptoms": "...", "prevention": "...", "cure": "..." }
}
```

Admin Pest Management and Register Insecticide screens now include separate English, Marathi and Hindi fields. Mobile result/history/pest-management screens read the farmer's selected language and display localized pest name, symptoms, prevention, cure, organic and chemical control with English fallback.

## Fixes: admin tab crash, Expo Go notification warning, mobile navbar, and 20 pest dataset

- Fixed React `useEffect` Promise cleanup crash in admin route screens by wrapping async loaders inside synchronous effects.
- Avoided loading `expo-notifications` in Expo Go; push notifications still require a development build, but Expo Go no longer triggers the same warning from our permission request path.
- Increased mobile bottom tab bar height/padding to prevent gesture navigation/footer overlap.
- Seeded the supplied 20 citrus pests into backend database with pest type, scientific name, damage, prevention, cure and Marathi/Hindi translation fields.
- Seeded the same 20 pest records as AI knowledge feed items and added all 20 classes to the AI model registry class list.

Note: The image classifier cannot be honestly trained without labelled pest/non-pest images. The 20 pest catalogue is now fed and ready; upload verified images per class from admin and click **Train Custom AI Model** to train the PyTorch classifier.

## 20-pest AI detection guarantee

The AI model registry and training pipeline are now locked to the supplied 20 citrus pest classes plus `no-citrus-pest`. Training runs in strict mode by default:

```env
STRICT_20_CLASS_TRAINING=true
```

This means the AI service will not register a production trained classifier unless verified training images exist for all 20 pest classes. Admin → Train AI now shows class coverage for every pest and the negative class. Upload labelled images per class, then train.

## Latest UX/error-handling updates

- Removed dashboard quick stats row.
- Removed About App and Terms cards from the dashboard menu; they remain accessible from Profile.
- Renamed mobile Year Calendar to **Calendar of Operation**.
- Admin Events screen now includes **Calendar of Operation** management for month-wise operations shown in mobile.
- Detection scan screen now hides confidence and shows severity only; full confidence remains available in saved full result/history.
- After pest detection, scan result now shows a **Management** section with tabs:
  - Preventive
  - Curative
- Mobile and admin panel now include Error Boundaries and friendlier API error messages.
- Backend and AI service now return structured JSON errors.
- Negative/no-pest responses are handled clearly in mobile scan and in admin farmer-upload review.
- Expo Go notification warning is avoided by not initializing notification permission flow inside Expo Go; development/production builds still support push notification setup.

## Latest reliability and UI updates

- Added password show/hide controls in mobile login/register and admin login/user/settings password fields.
- Added mobile blog list and blog details page.
- Added backend blog details API: `GET /blogs/{blog_id}`.
- Improved negative API handling for registration/login/password validation with readable errors.
- Improved mobile/admin API clients to parse structured backend errors.
- Wrapped key mobile and admin async API functions in try/catch and added error display/alerts.
- Detection scan result hides confidence and shows Management tabs for Preventive and Curative actions.

## PDF pest documentation ingestion

The uploaded `CitriSuraksha_Citrus_Pests.pdf` has been extracted and fed into the AI knowledge pipeline.

Stored files:

- `data/CitriSuraksha_Citrus_Pests.pdf`
- `data/citrus_pests_pdf_extracted.txt`
- `data/citrus_pests_pdf_knowledge.jsonl`
- `backend/app/pdf_knowledge.py`
- `ai-service/training-data/citrus_pests_pdf_knowledge.jsonl`

The backend seeds 20 PDF knowledge records into `ai_knowledge_items` on startup. The AI service also bootstraps the same PDF knowledge into its model-store knowledge file. Future Train AI jobs include this PDF knowledge together with verified pest images.

Important: this PDF trains the documentation/recommendation knowledge layer. The image classifier still needs labelled pest images for each of the 20 pest classes before a production visual model can be registered.

## Fix: passlib bcrypt version warning

If you see this startup warning:

```text
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

It is caused by `passlib==1.7.4` with newer `bcrypt` releases. The backend now pins:

```text
bcrypt==4.0.1
```

Rebuild backend dependencies:

```bash
docker compose build --no-cache backend
docker compose up
```

For local Python installs:

```bash
pip uninstall -y bcrypt
pip install bcrypt==4.0.1
```

## Latest fixes: pest detection fallback, profile/edit, notifications, blog social, calendar/search

- Fixed Pydantic protected namespace warning for `model_version`.
- AI service now has a 20-pest bootstrap fallback before a trained checkpoint exists: natural-looking pest/plant images return a preliminary 20-class pest result instead of only “not detected”; blank/non-natural images still return no-pest.
- Notification bell in mobile header is clickable and opens Events.
- Profile fields are read-only initially; user taps Edit to update. Logout asks confirmation.
- Mobile blog detail now supports likes and comments, backed by `/blogs/{id}/like` and `/blogs/{id}/comments`.
- Calendar of Operation months are clickable/expandable.
- Pest Guide includes search and data-not-available states.
- Dashboard cards are smaller and footer tab height was increased for gesture navigation.

## Latest admin/mobile UX and dataset-source updates

- Mobile notification bell now opens a dedicated Notifications page.
- Mobile Dashboard cards are smaller and footer padding increased further.
- Admin side route tabs are compact and no longer use sidebar scrolling.
- Added pagination/search reusable controls to admin users, farmers, pest registration/guide, blogs and events.
- Added 10 open-source dataset/repository URLs as AI knowledge/dataset source records on backend startup.
- Added `ai-service/training/download_open_datasets.py` to create a curated source manifest for license-reviewed dataset ingestion.
- AI bootstrap detection now returns a preliminary 20-pest result for natural-looking pest/plant images when no trained checkpoint is available, while still rejecting blank/non-pest images.

## Backup and migration between machines

Trained AI data and uploaded images are now portable. Important runtime data is stored in project folders and backed up with scripts:

- `storage/uploads/` - backend uploaded farmer/admin images
- `ai-service/model-store/` - trained model checkpoints, active model registry, TorchScript exports, AI jobs and knowledge
- `ai-service/training-data/` - curated manifests/PDF knowledge
- `data/` - imported PDFs and extracted data
- PostgreSQL is exported to `postgres.sql`

Windows backup:

```powershell
cd citrisurksha
.\scripts\backup.ps1
```

Windows restore on another machine:

```powershell
cd citrisurksha
.\scripts\restore.ps1 -BackupDir D:\CitriSurkshaBackup\backup-01
```

See `docs/MIGRATION_BACKUP_WINDOWS.md`.

## No-Docker deployment and speed improvements

CitriSurksha can now run without Docker on Windows/Linux using scripts in `scripts/`.

Windows:

```powershell
cd citrisurksha
copy .env.nodocker.example .env
.\scripts\start-ai-windows.ps1
.\scripts\start-backend-windows.ps1
.\scripts\start-admin-windows.ps1
```

Docs: `docs/NO_DOCKER_DEPLOYMENT.md`.

Performance updates:

- Backend and AI service use `ORJSONResponse` for faster JSON responses.
- GZip middleware is enabled for larger responses.
- Backend stores the original image but sends a compressed/resized JPEG to AI service for faster inference.
- AI service should run as one worker on CPU to avoid loading the model multiple times; backend can run multiple workers.

## Firebase push notifications

Firebase client configs were added for Android and iOS:

- `mobile/google-services.json`
- `mobile/GoogleService-Info.plist`

Mobile registers FCM token after login/register and saves it to backend. Admin Dashboard can send custom push notifications to all farmers. Creating an Event with notification enabled stores/sends notifications to farmers. Bell icon now opens notification screen and shows unseen count. Farmers can read, delete and clear notifications.

Backend sending requires a Firebase Admin SDK service account JSON, not just `google-services.json`:

```env
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

See `docs/FIREBASE_PUSH_NOTIFICATIONS.md`.

## Latest mobile updates: CIB-RC, blog HTML and Firebase Admin key

- Removed Profile card from mobile Dashboard menu. Profile remains in bottom navbar.
- Added **Recommended insecticides (CIB-RC)** dashboard card and mobile screen.
- Added backend endpoint `GET /insecticides` with farmer-safe CIB-RC disclaimer and pest-wise advisory options.
- Hidden confidence level from mobile scan, history and full detection detail screens.
- Blog details now render HTML using `react-native-webview` instead of stripping tags.
- Firebase Admin SDK service account file from upload was placed locally as `firebase-service-account.json` for backend push sending, and `.gitignore` excludes it. It is also excluded from generated zip for security.

## Latest admin/insecticide management improvements

- Recommended insecticides (CIB-RC) are now database-driven and managed from admin panel, not hardcoded in mobile.
- Added backend CRUD endpoints under `/insecticides/admin` and farmer endpoint `/insecticides`.
- Admin Register Insecticide is now route-based with list, add and edit screens.
- Farmer Uploads admin page now separates **New detections** and **Approved / Corrected** detections for high daily upload volume.
- Added reusable admin DataTable with search, pagination, Add, View modal, Edit and Enable/Disable actions; applied to the insecticide management flow and existing list pages progressively.

## Latest admin CRUD/tab restructuring

- Added separate Admin sidebar tab for **Calendar of Operation** (`/calendar-operation`).
- Removed Calendar of Operation management from the Events form.
- Events now have route-based list/add/edit pages.
- Pest Management now has route-based list/add/edit pages.
- User Management now has route-based list/add/edit pages.
- Register Insecticide already has route-based list/add/edit pages and is database-driven.
- Farmer Uploads separates New detections and Approved/Corrected uploads.

## Latest admin notification tabs

Added two new admin tabs:

- **Notification** (`/admin-notifications`) — admin receives alerts when a farmer sends chat, comments on blog, scans an image, or marks detection wrong.
- **Push Notification** (`/push-notifications`) — admin can send custom push notifications to all farmers and view push history with date, sent count and failed count.

Backend stores admin notifications in `admin_notifications` and push history in `push_notification_campaigns`.

## Latest admin usability improvements

- Detail modal now shows readable key/value sections instead of raw JSON.
- DataTable actions now use icons: 👁️ view, ✏️ edit, 🚫 disable, ✅ enable.
- Pagination now has a page number input with validation; users cannot navigate below page 1 or above total pages.
- Settings page theme selector now uses icon cards instead of a dropdown.
- Settings reset password UI now asks for current password, new password, and confirmation, with show/hide control.
- Added `/auth/change-password` API for secure self password changes.

## Latest fixes: push diagnostics and realtime chat

- Backend Firebase sender now also checks local `./firebase-service-account.json` fallback path, useful for Windows/no-Docker runs.
- Dashboard now shows `farmers_with_fcm_token` so failed push can be diagnosed; if zero, farmers have not registered FCM tokens yet or are using Expo Go instead of development build.
- Farmer/Admin chat now has a WebSocket endpoint `/chat/ws/{conversation_id}` and both mobile/admin chat screens listen for realtime replies.
- Farmer chat includes a simple chatbot first response before/admin escalation.

## Latest chat/Firebase/blog updates

- Farmer chat now keeps old conversations and includes a **Start New Chat** button.
- Farmer/admin chat supports file/image attachments and realtime WebSocket updates.
- Admin chat is inbox-style with realtime replies.
- Backend Firebase service account is now read directly from `backend/firebase-service-account.json` fallback path. The private file is excluded from zip/git.
- Blog management includes writer name and inline edit support with larger HTML editor.
- Mobile blog detail renders full HTML content via WebView and shows writer name from API when available.

## Firebase push debugging update

- Firebase service account can now be placed directly beside `backend/app/firebase_push.py` as `backend/app/firebase-service-account.json`.
- Backend logs Firebase initialization/send errors to `backend/app/logs/firebase_push.log`.
- Admin Push Notification tab shows Firebase status and recent logs.
- If push fails, check: service account initialized, farmers_with_fcm_token > 0, development/production mobile build installed, Android notification permission granted, and iOS APNs key uploaded in Firebase.

## Dynamic database config for Docker/no-Docker

Backend can now run from either project root or directly from `backend/` folder. It loads env from both:

- `citrisurksha/.env`
- `citrisurksha/backend/.env`

If you run without Docker and accidentally keep Docker hostname `postgres`, backend auto-converts it to `localhost` when `AUTO_LOCALHOST_DB_FALLBACK=true`.

Direct backend run on Windows:

```powershell
cd citrisurksha\backend
copy .env.example .env
# edit backend\.env database password
.\run_windows.ps1
```

See `docs/DYNAMIC_DATABASE_CONFIG.md`.

## Database switching and query verification

You can switch between SQLite and PostgreSQL using scripts:

```powershell
.\scripts\use-sqlite-windows.ps1
.\scripts\use-postgres-windows.ps1 -HostName localhost -Port 5432 -Database citrisurksha -User postgres -Password "YOUR_PASSWORD"
```

Run query smoke tests:

```powershell
.\scripts\check-queries-windows.ps1
```

Docs: `docs/DATABASE_SWITCHING_AND_QUERY_TESTS.md`.

## Researcher pest guide default data and image folder training

Researcher-provided English/Hindi/Marathi pest guide data is now stored by default in `backend/app/researcher_pest_guide.py`. On backend startup it is seeded into pest translations and AI knowledge records, so detection results can show richer identification, symptoms, preventive measures, biological management, chemical management and cure/IPM text.

Put labelled training images here:

```text
storage/training_images/<pest_id>/
```

Examples:

```text
storage/training_images/citrus-psyllid/
storage/training_images/citrus-leaf-miner/
storage/training_images/fruit-fly/
storage/training_images/no-citrus-pest/
```

After copying images into these folders, register them in DB:

```powershell
python scripts/register_training_folder.py
```

Then open Admin → Train AI and train the model. The researcher guide data is included in the AI knowledge records automatically.

## Production deployment guide

Deployment documentation for your target architecture is available at:

```text
docs/PRODUCTION_DEPLOYMENT.md
```

Target architecture covered:

- Backend API + AI service on VPS
- PostgreSQL/Redis on VPS or managed service
- Admin panel `dist/` on Hostinger
- Android/iOS mobile builds on Expo/EAS
- Firebase push notification setup
- Nginx reverse proxy and HTTPS
- Backup of trained AI data and uploads

Templates added:

```text
deploy/env/backend.production.env.example
deploy/env/admin.env.example
deploy/env/mobile.eas.env.example
deploy/nginx/citrisurksha-api.conf
deploy/systemd/citrisurksha-backend.service
deploy/systemd/citrisurksha-ai.service
deploy/hostinger/.htaccess
```

## Production readiness and credentials checklist

The old placeholder training script has been replaced. `ai-service/training/train.py` now calls the real PyTorch/TorchVision training engine in `ai-service/app/ml.py`.

Production keys/credentials checklist is documented here:

```text
docs/PRODUCTION_KEYS_AND_READINESS.md
```

## Python 3.13 PyTorch install fix

If installing AI requirements on Windows Python 3.13, use the updated `ai-service/requirements.txt` with:

```text
torch==2.6.0
torchvision==0.21.0
```

PyTorch 2.5.1 does not support Python 3.13. For Python 3.12, optional `ai-service/requirements-py312.txt` is provided.

See `docs/PYTHON_TORCH_INSTALL_WINDOWS.md`.

## Latest admin UI modernization

- Dashboard cards are now clickable and route to related modules.
- Admin panel UI was modernized with gradient dashboard hero, polished cards, hover effects, responsive tables and improved 4K/tablet/mobile breakpoints.
- Detail modal now shows readable sections instead of JSON.
- Actions use icons for view/edit/enable-disable/delete.
- Delete action added for platform users, farmers and pests.
- Farmer detection review now shows upload date and reviewed-by admin user.
- Farmer Chat inbox shows dates/realtime messages and supports attachments.

## Latest blog/chat/AI admin improvements

- Admin blog list now shows writer, views, likes, comments and date like a social feed metric row.
- Blog add and edit now open as separate route pages (`/blogs/add`, `/blogs/:id/edit`) instead of inline on the list.
- Blog add/edit includes a mobile preview pane.
- Mobile blog detail page was redesigned for long content, images, HTML, documents, likes, comments and views.
- Farmer/admin chat attachments are visible to both sides with downloadable/openable links.
- Train AI supports custom/new pest IDs from admin upload; missing pest records are created automatically as custom pests.
- Added AI Models tab to view trained model versions, progress percentage, active model and metrics.
- Farmer Uploads UI separates new vs approved/corrected uploads and shows reviewer info.

## Latest Farmer Upload and detail-date formatting fixes

- Farmer Upload review now shows farmer name, phone/user details and upload date for every detection.
- Clicking farmer name in Farmer Upload opens a readable farmer details modal.
- Admin detection review stores and shows which admin reviewed/corrected the detection and when.
- Detail modals now hide internal IDs and format date/time in normal Indian format instead of raw database timestamp.

## Latest branding update

- Added uploaded CitriSuraksha AI logo to mobile assets and admin assets.
- Mobile splash, login, register and header now use the logo.
- Admin login page now uses the logo with a premium design.
- Admin favicon is set to the logo via `admin-panel/public/favicon.png`.
- Mobile app icon/splash/adaptive icon now point to `mobile/assets/logo.png`.

## Final admin UI updates

- Removed emoji logo from dashboard/header; admin header now uses uploaded logo only.
- Removed Quick Push Notification from Dashboard; push sending remains in Push Notification tab.
- `farmers_with_fcm_token` dashboard card redirects to Farmer tab.
- Role-based admin navigation added: only admin sees User Management; support/agronomist/data-labeler see role-appropriate tabs.
- User Management password reset block removed.
- Farmer Chat now shows message date/time, WhatsApp-style bubbles, realtime WebSocket messages, and notification badges in sidebar.
- Sidebar Notification and Farmer Chat tabs show unread badges.
- Train AI tab redesigned and supports custom/new pest IDs.
- Blog list metrics and mobile preview retained; settings/admin UI spacing polished for responsive layouts.
