$ErrorActionPreference = "Stop"
$BackendEnv = Join-Path $PSScriptRoot "..\backend\.env"
if (!(Test-Path (Split-Path $BackendEnv))) { New-Item -ItemType Directory -Force -Path (Split-Path $BackendEnv) | Out-Null }
@"
APP_ENV=development
API_SECRET_KEY=change-me-long-random-secret
DATABASE_URL=sqlite:///./citrisurksha.db
AUTO_LOCALHOST_DB_FALLBACK=true
REDIS_URL=redis://localhost:6379/0
AI_SERVICE_URL=http://localhost:8100
UPLOAD_DIR=../storage/uploads
FIREBASE_SERVICE_ACCOUNT_PATH=./app/firebase-service-account.json
"@ | Out-File -Encoding utf8 $BackendEnv
Write-Host "Backend configured for SQLite: $BackendEnv"
Write-Host "Run: cd backend; .\run_windows.ps1"
