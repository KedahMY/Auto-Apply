@echo off
echo Stopping Auto-Apply...

set STOPPED=0

:: Kill anything listening on port 8000 (backend)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8000 "') do (
    taskkill /f /pid %%p >nul 2>&1
    echo Stopped backend (PID %%p)
    set STOPPED=1
)

:: Kill anything listening on port 5173 (frontend dev server)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":5173 "') do (
    taskkill /f /pid %%p >nul 2>&1
    echo Stopped frontend dev server (PID %%p)
    set STOPPED=1
)

if %STOPPED%==0 echo Nothing was running.
