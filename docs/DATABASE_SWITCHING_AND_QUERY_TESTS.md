# Database Switching and Query Tests

CitriSurksha supports both SQLite and PostgreSQL without code changes.

## Switch to SQLite on Windows

```powershell
cd citrisurksha
.\scripts\use-sqlite-windows.ps1
cd backend
.\run_windows.ps1
```

This writes `backend/.env` with:

```env
DATABASE_URL=sqlite:///./citrisurksha.db
```

## Switch to PostgreSQL on Windows

```powershell
cd citrisurksha
.\scripts\use-postgres-windows.ps1 -HostName localhost -Port 5432 -Database citrisurksha -User postgres -Password "YOUR_PASSWORD"
cd backend
.\run_windows.ps1
```

If you accidentally use Docker host `postgres` while running outside Docker, backend auto-converts it to `localhost` when:

```env
AUTO_LOCALHOST_DB_FALLBACK=true
```

## Dynamic DB config

You can use either `DATABASE_URL` or DB parts.

### Full URL

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/citrisurksha
```

### DB parts

If `DATABASE_URL` is empty/absent:

```env
DB_DRIVER=postgresql+psycopg2
DB_HOST=localhost
DB_PORT=5432
DB_NAME=citrisurksha
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
```

## Check active DB

```powershell
cd citrisurksha
.\scripts\check-db-windows.ps1
```

Or from admin API:

```http
GET /api/admin/system/database
```

## Query smoke tests

SQLite test:

```powershell
cd citrisurksha
.\scripts\check-queries-windows.ps1
```

PostgreSQL test with a test database:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/citrisurksha_test"
python .\scripts\check_backend_queries.py
```

The smoke test creates tables and verifies core query paths for users, pests, detections, blogs, likes, comments, events, calendar operations, insecticides, chat, notifications, feedback, training images/jobs and AI knowledge.

## Verified in workspace

The SQLite query smoke test passed and printed:

```text
ALL_BACKEND_QUERY_SMOKE_TESTS_PASSED
```
