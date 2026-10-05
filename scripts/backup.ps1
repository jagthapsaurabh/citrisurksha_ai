param(
  [string]$BackupDir = "backups\citrisurksha-backup-$(Get-Date -Format yyyyMMdd-HHmmss)"
)

$ErrorActionPreference = "Stop"
Write-Host "Creating CitriSurksha backup at $BackupDir"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Backup PostgreSQL database from running docker compose stack.
Write-Host "Exporting PostgreSQL database..."
docker compose exec -T postgres pg_dump -U citrisurksha -d citrisurksha --clean --if-exists | Out-File -Encoding utf8 "$BackupDir\postgres.sql"

# Backup uploaded farmer/admin images.
Write-Host "Copying uploaded images..."
if (Test-Path "storage\uploads") { Copy-Item -Recurse -Force "storage\uploads" "$BackupDir\uploads" }

# Backup trained AI model registry/checkpoints/knowledge.
Write-Host "Copying AI model-store..."
if (Test-Path "ai-service\model-store") { Copy-Item -Recurse -Force "ai-service\model-store" "$BackupDir\model-store" }

# Backup AI training data and curated source manifests.
Write-Host "Copying AI training-data..."
if (Test-Path "ai-service\training-data") { Copy-Item -Recurse -Force "ai-service\training-data" "$BackupDir\training-data" }

# Backup static imported data/PDFs.
Write-Host "Copying project data..."
if (Test-Path "data") { Copy-Item -Recurse -Force "data" "$BackupDir\data" }

# Save env and versions for reproducibility.
if (Test-Path ".env") { Copy-Item -Force ".env" "$BackupDir\.env" }
docker compose ps | Out-File -Encoding utf8 "$BackupDir\docker-compose-ps.txt"
@{
  created_at = (Get-Date).ToString("o")
  includes = @("postgres.sql", "uploads", "model-store", "training-data", "data", ".env")
  note = "Move this folder to another machine and run scripts/restore.ps1 -BackupDir <folder>."
} | ConvertTo-Json | Out-File -Encoding utf8 "$BackupDir\manifest.json"

Write-Host "Backup complete: $BackupDir"
