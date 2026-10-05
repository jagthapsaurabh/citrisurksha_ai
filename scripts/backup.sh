#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="${1:-backups/citrisurksha-backup-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$BACKUP_DIR"
echo "Creating backup at $BACKUP_DIR"
docker compose exec -T postgres pg_dump -U citrisurksha -d citrisurksha --clean --if-exists > "$BACKUP_DIR/postgres.sql"
[ -d storage/uploads ] && cp -a storage/uploads "$BACKUP_DIR/uploads"
[ -d ai-service/model-store ] && cp -a ai-service/model-store "$BACKUP_DIR/model-store"
[ -d ai-service/training-data ] && cp -a ai-service/training-data "$BACKUP_DIR/training-data"
[ -d data ] && cp -a data "$BACKUP_DIR/data"
[ -f .env ] && cp .env "$BACKUP_DIR/.env"
docker compose ps > "$BACKUP_DIR/docker-compose-ps.txt"
printf '{"created_at":"%s","note":"Restore with scripts/restore.sh %s"}\n' "$(date -Iseconds)" "$BACKUP_DIR" > "$BACKUP_DIR/manifest.json"
echo "Backup complete: $BACKUP_DIR"
