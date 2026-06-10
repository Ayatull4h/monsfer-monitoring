@echo off
:: Judul jendela
title Flask App Runner with Auto-Restart

:: Aktifkan UTF-8 untuk karakter Unicode
chcp 65001 >nul

:: Simpan direktori skrip
set SCRIPT_DIR=%~dp0

:: Nama folder virtual environment
set VENV_FOLDER=venv

:: Port yang digunakan oleh Flask
set FLASK_PORT=5002

:: Nama file Python utama
set APP_FILE=app.py

:: Tambahkan newline
echo.

:start
cls
echo [INFO] Memulai Flask App Runner...
echo =====================================================================
echo.

:: Pindah ke direktori skrip
cd /d "%SCRIPT_DIR%"

:: Cek apakah venv ada
if not exist "%VENV_FOLDER%" (
    echo [ERROR] Virtual environment '%VENV_FOLDER%' tidak ditemukan!
    echo Silakan buat venv terlebih dahulu dengan perintah:
    echo python -m venv %VENV_FOLDER%
    echo.
    echo Tekan tombol apa saja untuk keluar...
    pause >nul
    exit /b 1
)

:: Aktifkan venv
echo [INFO] Mengaktifkan virtual environment...
call "%VENV_FOLDER%\Scripts\activate.bat"

:: Cek apakah ada proses yang menggunakan port 5000
echo [INFO] Mencari proses yang menggunakan port %FLASK_PORT% (harus 5002)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%FLASK_PORT%') do set PID=%%a

:: Jika ada proses, hentikan
if defined PID (
    echo [INFO] Menemukan proses dengan PID: %PID%
    echo [INFO] Menghentikan proses yang menggunakan port %FLASK_PORT%...
    taskkill /F /PID %PID%
    echo.
)

:: Jalankan aplikasi Flask
echo [INFO] Menjalankan aplikasi Flask...
start "" /B python %APP_FILE%

echo.
echo =====================================================================
echo.
echo [READY] Aplikasi sedang berjalan di http://127.0.0.1:%FLASK_PORT% (PORT 5002)
echo         Tekan Ctrl+C untuk merestart aplikasi.
echo         Tekan Ctrl+Break untuk keluar dari script.
echo =====================================================================
echo.

:: Tunggu sampai user tekan Ctrl+C
pause >nul

:: Jika user tekan Ctrl+C, restart aplikasi
echo.
echo [INFO] Restarting aplikasi...
timeout /t 2 >nul
goto start