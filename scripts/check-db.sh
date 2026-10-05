#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv-api/bin/activate 2>/dev/null || true
python3 - <<'PY'
from backend.app.config import settings
from backend.app.db import engine
from sqlalchemy import inspect
print('DATABASE_URL =', settings.database_url)
print('DIALECT =', engine.dialect.name)
print('TABLES =', inspect(engine).get_table_names())
PY
