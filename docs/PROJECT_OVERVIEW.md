# CitriSuraksha AI — Project Overview

*Scan · Detect · Protect*
A complete citrus pest detection, advisory and surveillance platform for farmers, agriculture departments and research institutions.

---

## 1. What we have built

CitriSuraksha AI is **three connected products** that together form a complete citrus pest‑protection platform:

### A. Farmer Mobile App (Android + iOS)

- Login/registration with phone number, farm profile (village, crop, varieties, irrigation)
- **Scan** — take/upload a photo and get an AI diagnosis: pest name, severity, stage, symptoms, Preventive/Curative tabs with organic + chemical control, safety note
- **History** of every scan with review status (pending / verified / corrected by admin)
- **Pest Guide** — all 20 citrus pests with full management data
- **Calendar of Operation** (month‑wise orchard care), **Blog/advisories**, **Events**, **Recommended insecticides (CIB‑RC)**
- **Chat** (chatbot first, then real agronomist over WebSocket, with attachments)
- **Push notifications** (district pest alerts) via Firebase
- Full app in **English, Marathi, Hindi**

### B. Cloud Backend + AI Service

- FastAPI server with 12 API modules: auth, detections, pests, blogs, events, chat, insecticides, notifications, training, admin, etc.
- Stores every detection, feedback (correct/wrong), review, training image
- Separate AI service that trains and serves the vision model

### C. Admin & Expert Web Panel (15 modules, 4 roles)

- Dashboard KPIs, user/farmer management, **Farmer Uploads review** (verify/correct every AI result), pest & insecticide registry, blog/event/calendar publishing, **Train AI studio**, AI Models registry, **Firebase push campaigns** with logs, farmer chat, settings

---

## 2. What we use (technology stack)

| Layer | Technology (versions pinned in this repo) |
|---|---|
| Mobile app | **Expo SDK 54**, **React Native 0.81.5**, **React 19.1.0**, expo‑image‑picker, expo‑notifications, react‑navigation 7 |
| Backend API | **Python 3.13**, **FastAPI 0.115.6**, **Uvicorn**, **SQLAlchemy 2.0.36**, **PostgreSQL** (or SQLite), **python‑jose** (JWT), **passlib/bcrypt**, **Pillow**, **orjson**, **Redis** (optional cache) |
| Push | **firebase‑admin 6.6.0** (Firebase Cloud Messaging) |
| AI service | **PyTorch 2.6.0 + TorchVision 0.21.0**, **scikit‑learn**, **NumPy**, **Pillow** |
| Admin panel | **React + TypeScript + Vite**, react‑router‑dom |
| Knowledge | 33‑page scientific citrus pest compendium (PDF) + researcher‑written trilingual advisories, digitised into the database |

---

## 3. How the insect is detected from an image (exact pipeline in code)

1. **Capture** – farmer takes a photo (camera or gallery) in the app.
2. **Upload & validation** – backend accepts up to 20 MB, saves the original, then `prepare_ai_image()` **resizes it to max 1024 px JPEG (quality 82)** to keep inference fast and consistent.
3. **Call to AI service** – backend POSTs the image to `/predict` with a **25‑second timeout**.
4. **Pre‑processing** – the image is resized to **224×224**, converted to a tensor and **ImageNet‑normalised** (mean 0.485/0.456/0.406).
5. **Neural network** – a **convolutional neural network (CNN)** — by default **MobileNetV3‑Small** (ResNet18, MobileNetV3‑Large, EfficientNet‑B0 are selectable) — computes logits over **21 classes: the 20 citrus pests + a `no‑citrus‑pest` negative class**.
6. **Decision** – `softmax` turns logits into probabilities; the top class is accepted only if **confidence ≥ 0.55** (configurable). **Severity** is derived from confidence (≥0.85 high, ≥0.65 medium, else low). The response includes a **top‑5 list with confidences**, which the admin sees during review.
7. **Knowledge join** – the backend attaches the pest's full dossier (symptoms, prevention, cure, organic/chemical control, safety note) from the database in the farmer's language and saves the detection.
8. **Learning loop** – farmer marks *correct/wrong*; admin **verifies or corrects** each detection; "Approve & Train" turns it into a **labelled training image**. Training uses augmentation (random crop/flip/rotation/color‑jitter), a train/val split, and metrics; a new model version is only **registered if verified images exist for all 20 pest classes + negative class** (strict mode).

**Before real training images are uploaded**, the engine runs in a clearly‑labelled *bootstrap mode*: it checks the photo is a real plant/pest image (pixel variance and green/brown ratios — blank or document photos are rejected with "No citrus pest detected"), then returns a **deterministic preliminary result** from the 20‑pest catalogue so the app is fully usable, with the explanation *"Preliminary bootstrap detection… train with verified labelled images for accurate visual AI."* Once training completes, the real CNN takes over automatically.

---

## 4. Open source used — and what is *not* used

- **Frameworks/runtimes:** Python, Node.js, React, React Native, Expo, TypeScript, Vite — all open source (MIT/Apache/BSD).
- **AI/ML:** **PyTorch, TorchVision, scikit‑learn, NumPy, Pillow**. The network *architectures* (MobileNetV3, ResNet, EfficientNet) come from TorchVision's open‑source model zoo, but they are created with `weights=None` — i.e. **trained only on our own labelled images**, as the code comment states: *"weights=None ensures the pest model is trained on your own dataset… No paid/commercial AI API used."*
- **Server/data:** FastAPI, Uvicorn, SQLAlchemy, PostgreSQL, SQLite, Redis, Pillow, Pydantic, passlib/bcrypt, python‑jose, orjson.
- **Push:** Firebase Admin SDK (free tier; the SDK itself is open source).
- **Key point for the board:** there are **no paid AI services, no per‑scan API costs, and no vendor lock‑in** — every image, label and model stays on our servers.

---

*Companion materials: board pitch deck at `docs/pitch/CitriSuraksha_AI_Board_Pitch.pptx`, app screen captures at `docs/pitch/screens/`.*
