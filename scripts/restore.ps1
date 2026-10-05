param(
  [Parameter(Mandatory=$true)][string]$BackupDir
)

$ErrorActionPreference = "Stop"
if (!(Test-Path $BackupDir)) { throw "Backup directory not found: $BackupDir" }
Write-Host "Restoring CitriSurksha backup from $BackupDir"

New-Item -ItemType Directory -Force -Path "storage\uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "ai-service\model-store" | Out-Null
New-Item -ItemType Directory -Force -Path "ai-service\training-data" | Out-Null

if (Test-Path "$BackupDir\uploads") { Copy-Item -Recurse -Force "$BackupDir\uploads\*" "storage\uploads" }
if (Test-Path "$BackupDir\model-store") { Copy-Item -Recurse -Force "$BackupDir\model-store\*" "ai-service\model-store" }
if (Test-Path "$BackupDir\training-data") { Copy-Item -Recurse -Force "$BackupDir\training-data\*" "ai-service\training-data" }
if (Test-Path "$BackupDir\data") { Copy-Item -Recurse -Force "$BackupDir\data" "." }
if ((Test-Path "$BackupDir\.env") -and !(Test-Path ".env")) { Copy-Item -Force "$BackupDir\.env" ".env" }

Write-Host "Starting database container..."
docker compose up -d postgres
Start-Sleep -Seconds 5

if (Test-Path "$BackupDir\postgres.sql") {
  Write-Host "Restoring PostgreSQL database..."
  Get-Content "$BackupDir\postgres.sql" | docker compose exec -T postgres psql -U citrisurksha -d citrisurksha
}

Write-Host "Starting full stack..."
docker compose up -d --build
Write-Host "Restore complete. API: http://localhost:8080/api"
