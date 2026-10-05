# Windows Python / PyTorch install notes

## Why `torch==2.5.1` failed

You are using Python 3.13:

```text
C:\Python313
```

PyTorch 2.5.1 does not provide wheels for Python 3.13. That is why pip shows:

```text
ERROR: No matching distribution found for torch==2.5.1
```

## Fix applied

`ai-service/requirements.txt` now uses Python 3.13-compatible versions:

```text
torch==2.6.0
torchvision==0.21.0
```

## Recommended install on your machine

From project root:

```powershell
cd citrisurksha\ai-service
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If pip cache causes issues:

```powershell
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

## Alternative: use Python 3.12

If you want to use the older torch 2.5.1 stack, install Python 3.12 and run:

```powershell
py -3.12 -m venv .venv-ai
.\.venv-ai\Scripts\Activate.ps1
pip install -r requirements-py312.txt
```

## Verify

```powershell
python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__)"
```

Expected for Python 3.13:

```text
2.6.0 0.21.0
```

## Start AI service

From project root:

```powershell
cd citrisurksha
python -m uvicorn app.main:app --app-dir ai-service --host 127.0.0.1 --port 8100
```

Or from `ai-service` folder:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```
