@echo off
setlocal

echo Resetting Monsfer Simulation Stack...

:: Kill existing processes on ports 5102 and 5105
echo Killing existing processes on ports 5102 and 5105...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5102 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5105 ^| findstr LISTENING') do taskkill /f /pid %%a 2>nul

:: Kill all Python processes to ensure a clean start
echo Killing all Python processes...
taskkill /f /im python.exe /t 2>nul

:: Kill any stray cmd processes that might be holding log handles
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Monsfer*" 2>nul

echo Waiting for system to release file handles...
timeout /t 5 /nobreak >nul

:: Starting Gateway (5102)
echo Starting Gateway (5102)...
start "MonsferGateway" /b cmd /c "cd /d c:\Users\3KOM\monsfer_project_final\monsfer-server && venv\Scripts\python.exe server.py > gateway.log 2>&1"

:: Starting Monitoring UI (5105)
echo Starting Monitoring UI (5105)...
start "MonsferUI" /b cmd /c "cd /d c:\Users\3KOM\monsfer_project_final\monsfer-server\MONITORING_UI && ..\venv\Scripts\python.exe app.py > ui.log 2>&1"

:: Starting Simulator (Generates data)
echo Starting Simulator (Data Generator)...
start "MonsferSimulator" /b cmd /c "cd /d c:\Users\3KOM\monsfer_project_final\monsfer && ..\monsfer-server\venv\Scripts\python.exe auto_simulate.py > simulator.log 2>&1"

:: Starting Sync Agent (Uploads data)
echo Starting Sync Agent (Data Uploader)...
start "MonsferSync" /b cmd /c "cd /d c:\Users\3KOM\monsfer_project_final\monsfer && ..\monsfer-server\venv\Scripts\python.exe agent_sync.py > sync.log 2>&1"

echo.
echo All services started in background.
echo Gateway Log: monsfer-server\gateway.log
echo UI Log: monsfer-server\MONITORING_UI\ui.log
echo Simulator Log: monsfer\simulator.log
echo Sync Log: monsfer\sync.log
echo.
echo Please wait about 30 seconds for data to flow, then refresh http://127.0.0.1:5102/monitoring
pause
