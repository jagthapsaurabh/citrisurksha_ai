# CitriSurksha No-Docker Deployment

You can deploy without Docker. You need separate processes for:

1. Backend API: FastAPI on port 8000
2. AI service: FastAPI/PyTorch on port 8100
3. Admin panel: static build served by Nginx/IIS/Apache or `npm run dev` for testing
4. Mobile app: points to backend API URL
5. Database: SQLite quick start or native PostgreSQL for production
6. Redis: optional but recommended for speed

## Windows quick start without Docker

Open three PowerShell terminals.

### Terminal 1: AI service

```powershell
cd citrisurksha
.\scripts\start-ai-windows.ps1
```

### Terminal 2: Backend

```powershell
cd citrisurksha
copy .env.nodocker.example .env
.\scripts\start-backend-windows.ps1
```

### Terminal 3: Admin panel

```powershell
cd citrisurksha
.\scripts\start-admin-windows.ps1
```

URLs:

- Backend: `http://127.0.0.1:8000`
- AI service: `http://127.0.0.1:8100`
- Admin dev server: shown by Vite, usually `http://localhost:5173`

## Production Windows without Docker

Recommended:

- PostgreSQL installed as Windows service
- Redis for Windows alternative or Memurai/KeyDB/native Redis on WSL
- NSSM or Windows Services to run uvicorn processes
- IIS/Nginx reverse proxy with HTTPS
- Admin panel built with `npm run build` and served as static files

Backend service command:

```powershell
.\.venv-api\Scripts\uvicorn.exe app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 4
```

AI service command:

```powershell
.\.venv-ai\Scripts\uvicorn.exe app.main:app --app-dir ai-service --host 127.0.0.1 --port 8100 --workers 1
```

Keep AI workers at 1 on CPU to avoid loading the PyTorch model multiple times. Use more backend workers for API concurrency.

## Admin production build

```powershell
cd admin-panel
npm install
$env:VITE_API_URL="https://yourdomain.com/api"
npm run build
```

Serve `admin-panel/dist` with IIS/Nginx/Apache.

## Mobile API URL

```bash
EXPO_PUBLIC_API_URL=https://yourdomain.com/api npm start
```

For local no-Docker backend:

```bash
EXPO_PUBLIC_API_URL=http://YOUR_PC_IP:8000 npm start
```

## Performance checklist

- Use PostgreSQL, not SQLite, for multi-user production.
- Enable Redis.
- Run backend with 2-4 workers.
- Keep AI service model loaded in memory.
- Use SSD storage for `storage/uploads` and `ai-service/model-store`.
- Place Nginx/IIS reverse proxy in front with gzip enabled.
- Use HTTPS and HTTP/2.
