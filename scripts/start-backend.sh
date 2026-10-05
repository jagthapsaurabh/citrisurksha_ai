#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.nodocker.example .env
[ -d .venv-api ] || python3 -m venv .venv-api
source .venv-api/bin/activate
pip install -U pip
pip install -r backend/requirements.txt
export UPLOAD_DIR="$PWD/storage/uploads"
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 2
