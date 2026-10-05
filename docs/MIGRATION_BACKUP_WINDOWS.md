# CitriSurksha Backup, Restore and Machine Migration

This project stores trained AI data and uploaded images in portable project folders so you can move from one Windows machine to another.

## What must be migrated

| Data | Location / backup item | Why it matters |
|---|---|---|
| PostgreSQL database | `postgres.sql` | users, pests, detections, feedback, training records, admin corrections, blogs, events, chat |
| Uploaded images | `storage/uploads/` | farmer/admin images used for detection and training |
| Trained AI models | `ai-service/model-store/` | active model registry, checkpoints, TorchScript exports, knowledge store, jobs |
| AI training data | `ai-service/training-data/` | curated manifests and PDF/dataset knowledge |
| Imported PDFs/data | `data/` | CitriSurksha PDF and extracted knowledge records |
| Environment | `.env` | service URLs/secrets/local settings |

## Windows backup

Run from project root:

```powershell
cd citrisurksha
.\scripts\backup.ps1
```

This creates a folder like:

```text
backups\citrisurksha-backup-20260701-153000
```

You can also choose a path:

```powershell
.\scripts\backup.ps1 -BackupDir D:\CitriSurkshaBackup\backup-01
```

## Windows restore on another machine

1. Install Docker Desktop and Node.js.
2. Copy the project folder and backup folder to the new machine.
3. Run:

```powershell
cd citrisurksha
copy .env.example .env
.\scripts\restore.ps1 -BackupDir D:\CitriSurkshaBackup\backup-01
```

The restore script copies uploads/model data and restores PostgreSQL using `psql` inside the Docker container.

## Linux/macOS backup

```bash
cd citrisurksha
./scripts/backup.sh
```

## Linux/macOS restore

```bash
cd citrisurksha
./scripts/restore.sh backups/citrisurksha-backup-YYYYMMDD-HHMMSS
```

## Current storage design

`docker-compose.yml` now stores backend uploads in a bind-mounted folder:

```yaml
./storage/uploads:/app/uploads
```

AI trained models are already stored in:

```yaml
./ai-service/model-store:/app/model-store
```

This makes the important files visible on Windows and easy to back up.

## After restore checklist

```powershell
docker compose up -d --build
curl http://localhost:8080/api/health
curl http://localhost:8080/ai/health
```

Open admin and check:

- Train AI jobs
- Class coverage
- Detection history images
- Active model status

## Notes

- Do not rely only on Docker volumes for migration.
- Always use the backup script before moving machines.
- For production, store backups in cloud storage and encrypt them.
