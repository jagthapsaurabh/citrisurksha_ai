#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv-ai ] || python3 -m venv .venv-ai
source .venv-ai/bin/activate
pip install -U pip
pip install -r ai-service/requirements.txt
export MODEL_STORE="$PWD/ai-service/model-store"
export FORCE_CPU=true
export TORCH_NUM_THREADS=8
uvicorn app.main:app --app-dir ai-service --host 127.0.0.1 --port 8100 --workers 1
