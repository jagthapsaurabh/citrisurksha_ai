param(
  [string]$HostName = "localhost",
  [int]$Port = 5432,
  [string]$Database = "citrisurksha",
  [string]$User = "postgres",
  [Parameter(Mandatory=$true)][string]$Password
)
$ErrorActionPreference = "Stop"
$BackendEnv = Join-Path $PSScriptRoot "..\backend\.env"
if (!(Test-Path (Split-Path $BackendEnv))) { New-Item -ItemType Directory -Force -Path (Split-Path $BackendEnv) | Out-Null }
# URL encode only the password part.
Add-Type -AssemblyName System.Web
$EncodedPassword = [System.Web.HttpUtility]::UrlEncode($Password)
@"
APP_ENV=development
API_SECRET_KEY=change-me-long-random-secret
DATABASE_URL=postgresql+psycopg2://$User`:$EncodedPassword@$HostName`:$Port/$Database
AUTO_LOCALHOST_DB_FALLBACK=true
REDIS_URL=redis://localhost:6379/0
AI_SERVICE_URL=http://localhost:8100
UPLOAD_DIR=../storage/uploads
FIREBASE_SERVICE_ACCOUNT_PATH=./app/firebase-service-account.json
"@ | Out-File -Encoding utf8 $BackendEnv
Write-Host "Backend configured for PostgreSQL: $BackendEnv"
Write-Host "Database URL host: $HostName port: $Port database: $Database user: $User"
Write-Host "Make sure database exists. Example in psql: CREATE DATABASE $Database;"
Write-Host "Run: cd backend; .\run_windows.ps1"
