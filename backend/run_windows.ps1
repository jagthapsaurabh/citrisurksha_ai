$ErrorActionPreference = "Stop"
# Run from backend folder: .\run_windows.ps1
if (!(Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created backend\.env from backend\.env.example. Edit DATABASE_URL/password if needed."
}
if (!(Test-Path "..\.venv-api")) { py -3.12 -m venv ..\.venv-api }
. ..\.venv-api\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
