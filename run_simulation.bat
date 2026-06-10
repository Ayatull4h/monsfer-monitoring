@echo off
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%monsfer-server\venv\Scripts\python.exe"
set "UI_DIR=%ROOT%monsfer-server\MONITORING_UI"
set "SERVER_DIR=%ROOT%monsfer-server"
set "SIM_DIR=%ROOT%monsfer"

echo ============================================
echo   MONSFER SIMULATION STACK - STARTING
echo ============================================
echo.

REM ---- Kill existing instances ----
echo [1/4] Menghentikan proses lama...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5102 " 2^>nul') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5105 " 2^>nul') do (
    if not "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM ---- Start Gateway (port 5102) ----
echo [2/4] Menjalankan Gateway (port 5102)...
start "Monsfer Gateway 5102" /D "%SERVER_DIR%" "%VENV%" server.py

timeout /t 3 /nobreak >nul

REM ---- Start Monitoring UI (port 5105) ----
echo [3/4] Menjalankan Monitoring UI (port 5105)...
start "Monsfer UI 5105" /D "%UI_DIR%" "%VENV%" app.py

timeout /t 3 /nobreak >nul

REM ---- Start Simulator + Sync Agent ----
echo [4/4] Menjalankan Simulator dan Sync Agent...
start "Monsfer Simulator" /D "%SIM_DIR%" "%VENV%" auto_simulate.py
timeout /t 2 /nobreak >nul
start "Monsfer Sync" /D "%SIM_DIR%" "%VENV%" agent_sync.py

echo.
echo ============================================
echo   SEMUA SERVICE BERJALAN!
echo   Gateway  : http://127.0.0.1:5102
echo   UI       : http://127.0.0.1:5105  
echo   Monitoring: http://127.0.0.1:5102/monitoring
echo ============================================
echo.
echo.
echo Membuka browser secara otomatis...
start "" "http://127.0.0.1:5105/monitoring"
