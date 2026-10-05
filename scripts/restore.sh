#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="${1:?Usage: scripts/restore.sh <backup-dir>}"
[ -d "$BACKUP_DIR" ] || { echo "Backup directory not found: $BACKUP_DIR"; exit 1; }
mkdir -p storage/uploads ai-service/model-store ai-service/training-data
[ -d "$BACKUP_DIR/uploads" ] && cp -a "$BACKUP_DIR/uploads/." storage/uploads/
[ -d "$BACKUP_DIR/model-store" ] && cp -a "$BACKUP_DIR/model-store/." ai-service/model-store/
[ -d "$BACKUP_DIR/training-data" ] && cp -a "$BACKUP_DIR/training-data/." ai-service/training-data/
[ -d "$BACKUP_DIR/data" ] && cp -a "$BACKUP_DIR/data" .
[ -f "$BACKUP_DIR/.env" ] && [ ! -f .env ] && cp "$BACKUP_DIR/.env" .env
docker compose up -d postgres
sleep 5
[ -f "$BACKUP_DIR/postgres.sql" ] && docker compose exec -T postgres psql -U citrisurksha -d citrisurksha < "$BACKUP_DIR/postgres.sql"
docker compose up -d --build
echo "Restore complete."
