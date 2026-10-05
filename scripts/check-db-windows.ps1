$ErrorActionPreference = "Stop"
cd "$PSScriptRoot\.."
if (!(Test-Path ".venv-api")) { py -3.12 -m venv .venv-api }
. .\.venv-api\Scripts\Activate.ps1
python - <<'PY'
from backend.app.config import settings
from backend.app.db import engine
from sqlalchemy import inspect
print('DATABASE_URL =', settings.database_url)
print('DIALECT =', engine.dialect.name)
print('TABLES =', inspect(engine).get_table_names())
PY
