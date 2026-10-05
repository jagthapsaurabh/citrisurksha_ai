$ErrorActionPreference = "Stop"
cd "$PSScriptRoot\.."
if (!(Test-Path ".venv-ai")) { py -3.12 -m venv .venv-ai }
. .\.venv-ai\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\ai-service\requirements.txt
$env:MODEL_STORE = "$PWD\ai-service\model-store"
$env:FORCE_CPU = "true"
$env:TORCH_NUM_THREADS = "8"
uvicorn app.main:app --app-dir .\ai-service --host 127.0.0.1 --port 8100 --workers 1
