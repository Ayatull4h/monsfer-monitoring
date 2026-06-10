@echo off
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%monsfer-server\venv\Scripts\python.exe"
set "UI_DIR=%ROOT%monsfer-server\MONITORING_UI"
set "SERVER_DIR=%ROOT%monsfer-server"

echo ============================================
echo   MONSFER SERVERS - STARTING (NO SIMULATION)
echo ============================================
echo.

REM ---- Kill existing instances ----
echo [1/3] Menghentikan proses lama...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5102 " 2^>nul') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5105 " 2^>nul') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)
ping 127.0.0.1 -n 3 >nul

REM ---- Start Gateway (port 5102) ----
echo [2/3] Menjalankan Gateway (port 5102)...
start "MonsferGateway" /b cmd /c "cd /d %SERVER_DIR% && venv\Scripts\python.exe server.py > gateway.log 2>&1"

ping 127.0.0.1 -n 4 >nul

REM ---- Start Monitoring UI (port 5105) ----
echo [3/3] Menjalankan Monitoring UI (port 5105)...
start "MonsferUI" /b cmd /c "cd /d %UI_DIR% && ..\venv\Scripts\python.exe app.py > ui.log 2>&1"

echo.
echo ============================================
echo   SERVERS BERJALAN!
echo   Gateway  : http://127.0.0.1:5102 (Listen to SDR uploads)
echo   UI       : http://127.0.0.1:5105
echo   Monitoring Dashboard: http://127.0.0.1:5102/monitoring
echo ============================================
echo.
