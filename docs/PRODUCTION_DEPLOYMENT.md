# CitriSurksha Production Deployment Guide

Target setup:

1. **Backend API + AI service on one VPS**
2. **Admin panel static `dist/` on Hostinger**
3. **Mobile Android/iOS builds through Expo/EAS**
4. **PostgreSQL database on VPS or managed DB**
5. **Firebase push notifications**

Example public URLs used in this guide:

```text
API domain: https://api.yourdomain.com/api
Admin domain: https://admin.yourdomain.com
```

Replace these with your real domains.

---

## 1. Backend VPS deployment

### 1.1 Server requirements

Recommended minimum VPS:

```text
Ubuntu 22.04/24.04
4 vCPU minimum, 8 vCPU recommended
8 GB RAM minimum, 16 GB recommended if AI training runs on same server
80+ GB SSD
Python 3.12 recommended
PostgreSQL 15/16
Redis
Nginx
```

For CPU AI inference/training, keep AI service workers at `1` to avoid loading the PyTorch model multiple times.

---

## 2. Install system packages on VPS

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib redis-server nginx git build-essential libpq-dev
```

Enable services:

```bash
sudo systemctl enable postgresql redis-server nginx
sudo systemctl start postgresql redis-server nginx
```

---

## 3. Create PostgreSQL database

```bash
sudo -u postgres psql
```

Inside psql:

```sql
CREATE DATABASE citrisurksha;
CREATE USER citrisurksha WITH PASSWORD 'CHANGE_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE citrisurksha TO citrisurksha;
ALTER DATABASE citrisurksha OWNER TO citrisurksha;
\q
```

---

## 4. Upload project to VPS

Recommended path:

```text
/var/www/citrisurksha
```

Example:

```bash
sudo mkdir -p /var/www/citrisurksha
sudo chown -R $USER:$USER /var/www/citrisurksha
cd /var/www/citrisurksha
# upload/copy project files here, or git clone your private repo
```

Create runtime folders:

```bash
mkdir -p storage/uploads ai-service/model-store ai-service/training-data backend/app/logs
```

---

## 5. Backend environment file

Create:

```bash
nano /var/www/citrisurksha/.env
```

Example:

```env
APP_ENV=production
API_SECRET_KEY=CHANGE_TO_LONG_RANDOM_SECRET
DATABASE_URL=postgresql+psycopg2://citrisurksha:CHANGE_STRONG_PASSWORD@127.0.0.1:5432/citrisurksha
REDIS_URL=redis://127.0.0.1:6379/0
AI_SERVICE_URL=http://127.0.0.1:8100
UPLOAD_DIR=/var/www/citrisurksha/storage/uploads
FIREBASE_SERVICE_ACCOUNT_PATH=/var/www/citrisurksha/backend/app/firebase-service-account.json
ACCESS_TOKEN_MINUTES=10080
FORCE_CPU=true
TORCH_NUM_THREADS=8
PEST_CONFIDENCE_THRESHOLD=0.55
STRICT_20_CLASS_TRAINING=true
MIN_IMAGES_PER_PEST=1
```

Template exists at:

```text
deploy/env/backend.production.env.example
```

---

## 6. Firebase backend service account

The mobile `google-services.json` and `GoogleService-Info.plist` are client configs. Backend push sending needs Firebase Admin SDK service account.

Firebase Console:

```text
Project Settings → Service Accounts → Generate new private key
```

Save on VPS:

```text
/var/www/citrisurksha/backend/app/firebase-service-account.json
```

Secure it:

```bash
chmod 600 /var/www/citrisurksha/backend/app/firebase-service-account.json
```

---

## 7. Python virtual environments

### Backend venv

```bash
cd /var/www/citrisurksha
python3 -m venv .venv-api
source .venv-api/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### AI service venv

```bash
cd /var/www/citrisurksha
python3 -m venv .venv-ai
source .venv-ai/bin/activate
pip install --upgrade pip
pip install -r ai-service/requirements.txt
```

PyTorch install can be large. If needed, install CPU wheel manually from PyTorch instructions.

---

## 8. Test manually before systemd

Terminal 1:

```bash
cd /var/www/citrisurksha
source .venv-ai/bin/activate
MODEL_STORE=/var/www/citrisurksha/ai-service/model-store FORCE_CPU=true TORCH_NUM_THREADS=8 \
uvicorn app.main:app --app-dir ai-service --host 127.0.0.1 --port 8100 --workers 1
```

Terminal 2:

```bash
cd /var/www/citrisurksha
source .venv-api/bin/activate
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 4
```

Check:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8100/health
```

On first startup, backend creates DB tables and seeds pest/default data.

---

## 9. Systemd services

Templates are included:

```text
deploy/systemd/citrisurksha-backend.service
deploy/systemd/citrisurksha-ai.service
```

Copy:

```bash
sudo cp deploy/systemd/citrisurksha-backend.service /etc/systemd/system/
sudo cp deploy/systemd/citrisurksha-ai.service /etc/systemd/system/
```

Set ownership:

```bash
sudo chown -R www-data:www-data /var/www/citrisurksha
```

Reload/start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable citrisurksha-ai citrisurksha-backend
sudo systemctl start citrisurksha-ai citrisurksha-backend
```

Check logs:

```bash
sudo journalctl -u citrisurksha-backend -f
sudo journalctl -u citrisurksha-ai -f
```

---

## 10. Nginx reverse proxy

Template:

```text
deploy/nginx/citrisurksha-api.conf
```

Edit domain:

```nginx
server_name api.yourdomain.com;
```

Copy:

```bash
sudo cp deploy/nginx/citrisurksha-api.conf /etc/nginx/sites-available/citrisurksha-api.conf
sudo ln -s /etc/nginx/sites-available/citrisurksha-api.conf /etc/nginx/sites-enabled/citrisurksha-api.conf
sudo nginx -t
sudo systemctl reload nginx
```

Install SSL:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

Public API becomes:

```text
https://api.yourdomain.com/api
```

Media:

```text
https://api.yourdomain.com/media/...
```

---

## 11. Admin panel deployment on Hostinger

Admin is a static Vite app. Build it with production API URL.

On your local machine:

```bash
cd citrisurksha/admin-panel
npm install
```

Windows PowerShell:

```powershell
$env:VITE_API_URL="https://api.yourdomain.com/api"
npm run build
```

Linux/macOS:

```bash
VITE_API_URL=https://api.yourdomain.com/api npm run build
```

Upload contents of:

```text
admin-panel/dist/
```

to Hostinger public folder, for example:

```text
public_html/
```

For route refresh support, upload this file too:

```text
deploy/hostinger/.htaccess
```

to the same folder as `index.html`.

Admin login points to:

```text
https://api.yourdomain.com/api
```

---

## 12. Mobile build on Expo/EAS

Mobile needs API URL at build time.

Set EAS environment variable:

```text
EXPO_PUBLIC_API_URL=https://api.yourdomain.com/api
```

You can set it in Expo dashboard or locally before build.

### Android development/internal build

```bash
cd citrisurksha/mobile
npm install
eas build --profile development --platform android
```

### iOS development/internal build

```bash
eas build --profile development --platform ios
```

### Production builds

```bash
eas build --profile production --platform android
eas build --profile production --platform ios
```

Or both:

```bash
eas build --profile production --platform all
```

---

## 13. Firebase mobile files

These must exist before EAS build:

```text
mobile/google-services.json
mobile/GoogleService-Info.plist
```

Configured in `mobile/app.json`:

```json
"android": {
  "package": "com.citrisurksha.app",
  "googleServicesFile": "./google-services.json"
},
"ios": {
  "bundleIdentifier": "com.citrisurksha.app",
  "googleServicesFile": "./GoogleService-Info.plist"
}
```

For iOS push, configure APNs key in Firebase Console.

---

## 14. Push notification checklist

Backend:

```text
/var/www/citrisurksha/backend/app/firebase-service-account.json
```

`.env`:

```env
FIREBASE_SERVICE_ACCOUNT_PATH=/var/www/citrisurksha/backend/app/firebase-service-account.json
```

Admin panel:

```text
Push Notification → Firebase Status
```

Check:

```text
Firebase initialized: Yes
Credential found: 1
farmers_with_fcm_token > 0
```

If farmers_with_fcm_token is 0, mobile builds are not registering FCM tokens. Test with development/production build, not Expo Go.

---

## 15. Train AI data persistence

Persist/migrate these folders:

```text
storage/uploads/
ai-service/model-store/
ai-service/training-data/
data/
```

Use backup script:

```bash
./scripts/backup.sh
```

Windows:

```powershell
.\scripts\backup.ps1
```

---

## 16. Health checks after deployment

```bash
curl https://api.yourdomain.com/health
curl https://api.yourdomain.com/api/health
curl https://api.yourdomain.com/ai/health
```

Note: Nginx template maps `/api/` to backend root, so backend `/health` can be available as:

```text
https://api.yourdomain.com/api/health
```

---

## 17. Common problems

### Admin works locally but not on Hostinger refresh

Upload `.htaccess` from:

```text
deploy/hostinger/.htaccess
```

### Mobile cannot call API

Check build-time value:

```text
EXPO_PUBLIC_API_URL=https://api.yourdomain.com/api
```

Rebuild app after changing it.

### Push failed

Check Admin → Push Notification → Firebase Status/Logs.

### PostgreSQL no tables

Check backend active DB:

```http
GET /api/admin/system/database
```

Make sure VPS `.env` is loaded and not using SQLite.

### AI slow

Use smaller image uploads, keep AI workers at 1, use SSD, increase CPU/RAM, or move AI service to GPU server later.
