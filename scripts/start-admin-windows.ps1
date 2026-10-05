$ErrorActionPreference = "Stop"
cd "$PSScriptRoot\..\admin-panel"
npm install
$env:VITE_API_URL = "http://127.0.0.1:8000"
npm run dev
