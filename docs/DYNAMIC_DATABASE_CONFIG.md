# Dynamic Database Configuration: Docker and No-Docker

CitriSurksha backend can now run correctly from either:

1. Docker Compose project root
2. Directly from the `backend/` folder on Windows/Linux

## Env loading order

Backend loads env files using absolute paths:

```text
citrisurksha/.env
citrisurksha/backend/.env
```

Actual OS environment variables override both files.

## Option A: Use DATABASE_URL directly

### Docker Compose

Inside Docker Compose, service hostname is `postgres`:

```env
DATABASE_URL=postgresql+psycopg2://citrisurksha:citrisurksha@postgres:5432/citrisurksha
```

### No-Docker Windows / local PostgreSQL

When running directly on Windows, use `localhost` or `127.0.0.1`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/citrisurksha
```

If you accidentally keep `@postgres:5432` while running outside Docker, backend now automatically converts it to `@localhost:5432` when:

```env
AUTO_LOCALHOST_DB_FALLBACK=true
```

## Option B: Use DB_* variables

If `DATABASE_URL` is absent, backend builds it from:

```env
DB_DRIVER=postgresql+psycopg2
DB_HOST=localhost
DB_PORT=5432
DB_NAME=citrisurksha
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
```

For SQLite quick test:

```env
DB_DRIVER=sqlite
```

or:

```env
DATABASE_URL=sqlite:///./citrisurksha.db
```

## Running directly from backend folder

```powershell
cd citrisurksha\backend
copy .env.example .env
# edit backend\.env with your DB password
.\run_windows.ps1
```

or manually:

```powershell
cd citrisurksha\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Running from project root

```powershell
cd citrisurksha
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

## Check active DB

After login as admin:

```http
GET /api/admin/system/database
```

Or run:

```powershell
.\scripts\check-db-windows.ps1
```

It prints active `DATABASE_URL`, dialect and tables.

## Why tables were missing

If registration worked but PostgreSQL had no tables, backend was likely connected to SQLite. Now backend auto-loads env more reliably and can fallback Docker hostname to localhost outside Docker.
