@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "BASE_DIR=%~dp0monsfer"
set "CMD=%1"
if "%CMD%"=="" set "CMD=start"

if /i "%CMD%"=="start" goto :start
if /i "%CMD%"=="stop" goto :stop
if /i "%CMD%"=="status" goto :status
if /i "%CMD%"=="restart" goto :restart
echo Usage: %~nx0 {start^|stop^|status^|restart}
exit /b 1

:start
echo Starting all SDR agents...
for %%a in (
    "agent_acquisition.py|acquisition"
    "agent_health.py|health"
    "agent_wifi.py|wifi"
    "agent_sync.py|sync"
) do (
    for /f "tokens=1,2 delims=|" %%x in (%%a) do (
        set "script=%%x"
        set "name=%%y"
        set "pid_file=%BASE_DIR%\%%y.pid"
        if exist "!pid_file!" (
            set /p oldpid=<"!pid_file!"
            tasklist /fi "PID eq !oldpid!" 2>nul | find "!oldpid!" >nul
            if !errorlevel! equ 0 (
                echo   [SKIP] !name! already running (PID: !oldpid!)
                goto :next_%%y
            )
        )
        start "monsfer-%%y" /B "%BASE_DIR%\venv\Scripts\python.exe" "%BASE_DIR%\%%x"
        echo !ERRORLEVEL! > "%BASE_DIR%\%%y.pid"
        :: Can't reliably get PID in cmd, so just note it started
        echo   [START] !name!
        :next_%%y
    )
)
echo Done.
exit /b 0

:stop
echo Stopping all SDR agents...
for %%a in (
    "acquisition|agent_acquisition.py"
    "health|agent_health.py"
    "wifi|agent_wifi.py"
    "sync|agent_sync.py"
) do (
    for /f "tokens=1,2 delims=|" %%x in (%%a) do (
        set "name=%%x"
        set "script=%%y"
        set "pid_file=%BASE_DIR%\%%x.pid"
        if exist "!pid_file!" (
            set /p oldpid=<"!pid_file!"
            taskkill /f /pid !oldpid! >nul 2>&1
            if !errorlevel! equ 0 (
                echo   [STOP] !name!
            ) else (
                echo   [STOP] !name! (not running)
            )
            del "!pid_file!" 2>nul
        ) else (
            echo   [SKIP] !name! (no pid file)
        )
        :: Also kill any stray python running that script
        taskkill /f /fi "WINDOWTITLE eq monsfer-%%x" >nul 2>&1
    )
)
:: Kill any remaining python windows with monsfer title
taskkill /f /fi "WINDOWTITLE eq monsfer-*" >nul 2>&1
echo Done.
exit /b 0

:status
echo SDR Agent Status:
echo -----------------
for %%a in (
    "acquisition|agent_acquisition.py"
    "health|agent_health.py"
    "wifi|agent_wifi.py"
    "sync|agent_sync.py"
) do (
    for /f "tokens=1,2 delims=|" %%x in (%%a) do (
        set "name=%%x"
        set "pid_file=%BASE_DIR%\%%x.pid"
        if exist "!pid_file!" (
            set /p oldpid=<"!pid_file!"
            tasklist /fi "PID eq !oldpid!" 2>nul | find "!oldpid!" >nul
            if !errorlevel! equ 0 (
                echo   [RUNNING] !name! (PID: !oldpid!)
            ) else (
                echo   [STOPPED] !name! (stale pid)
            )
        ) else (
            echo   [STOPPED] !name!
        )
    )
)
exit /b 0

:restart
call :stop
timeout /t 2 /nobreak >nul
call :start
exit /b 0
