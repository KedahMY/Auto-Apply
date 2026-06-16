@echo off
setlocal
set ROOT=%~dp0
set UVICORN=%ROOT%.venv\Scripts\uvicorn.exe

echo Auto-Apply
echo ==========

:: Guard: venv must exist
if not exist "%UVICORN%" (
    echo ERROR: .venv not found.
    echo Run:   python -m venv .venv
    echo        .venv\Scripts\pip install -r backend\requirements.txt
    exit /b 1
)

:: Guard: .env must exist
if not exist "%ROOT%backend\.env" (
    echo ERROR: backend\.env not found.
    echo Copy the template and fill in DEEPSEEK_API_KEY.
    exit /b 1
)

:: Guard: already running
netstat -ano | findstr "LISTENING" | findstr ":8000 " >nul 2>&1
if %errorlevel%==0 (
    echo Already running at http://localhost:8000
    start http://localhost:8000
    exit /b 0
)

:: Build frontend if dist is missing
if not exist "%ROOT%frontend\dist\index.html" (
    echo Building frontend...
    cd /d "%ROOT%frontend"
    call npm run build
    if errorlevel 1 (
        echo ERROR: frontend build failed.
        exit /b 1
    )
)

:: Start backend in a new window
echo Starting backend...
start "Auto-Apply Backend" cmd /k "cd /d "%ROOT%backend" && "%UVICORN%" api.server:app --port 8000"

:: Wait for the server to be ready then open browser
timeout /t 3 /nobreak >nul
start http://localhost:8000
echo Open: http://localhost:8000
