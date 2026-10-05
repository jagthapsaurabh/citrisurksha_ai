$ErrorActionPreference = "Stop"
cd "$PSScriptRoot\.."
if (!(Test-Path ".env")) { Copy-Item .env.nodocker.example .env }
if (!(Test-Path ".venv-api")) { py -3.12 -m venv .venv-api }
. .\.venv-api\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\backend\requirements.txt
$env:UPLOAD_DIR = "$PWD\storage\uploads"
uvicorn app.main:app --app-dir .\backend --host 127.0.0.1 --port 8000 --workers 2
