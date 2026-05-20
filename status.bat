@echo off
echo Auto-Apply Status
echo =================

:: Backend (port 8000) — store PID in variable to avoid nested-parens issue
set BACKEND_PID=
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8000 "') do set BACKEND_PID=%%p

if defined BACKEND_PID (
    echo [ON]  Backend         http://localhost:8000   PID %BACKEND_PID%
) else (
    echo [OFF] Backend         port 8000 not listening
)

:: Frontend dev server (port 5173)
set FRONTEND_PID=
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":5173 "') do set FRONTEND_PID=%%p

if defined FRONTEND_PID (
    echo [ON]  Frontend dev    http://localhost:5173   PID %FRONTEND_PID%
) else (
    echo [OFF] Frontend dev    port 5173 not listening
)

:: Frontend build
if exist "%~dp0frontend\dist\index.html" (
    echo [OK]  Frontend build  frontend\dist\ exists
) else (
    echo [--]  Frontend build  missing - run: cd frontend ^&^& npm run build
)

:: .env
if exist "%~dp0backend\.env" (
    echo [OK]  backend\.env    found
) else (
    echo [--]  backend\.env    MISSING
)
