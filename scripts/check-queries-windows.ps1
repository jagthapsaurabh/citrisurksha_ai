$ErrorActionPreference = "Stop"
cd "$PSScriptRoot\.."
if (!(Test-Path ".venv-api")) { py -3.12 -m venv .venv-api }
. .\.venv-api\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
python .\scripts\check_backend_queries.py
Write-Host "SQLite query smoke test completed."
Write-Host "For PostgreSQL test, run with TEST_DATABASE_URL env var, e.g.:"
Write-Host '$env:TEST_DATABASE_URL="postgresql+psycopg2://postgres:pass@localhost:5432/citrisurksha_test"; python .\scripts\check_backend_queries.py'
