@echo off
echo Stopping all Monsfer processes...
taskkill /F /IM python.exe /T
timeout /t 2 /nobreak > nul

echo Cleaning up old simulation data...
del /Q monsfer\data_upload\*
del /Q monsfer-server\userdata\temporary\*

echo Starting Monsfer Simulation...
start /B .\run_simulation.bat

echo Simulation restarted.
echo Gateway: http://localhost:5102
echo Monitoring UI: http://localhost:5105
