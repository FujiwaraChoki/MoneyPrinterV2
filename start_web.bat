@echo off
title MoneyPrinter V2 - Retro UI
color 0A

echo =========================================
echo    MoneyPrinter V2 - Retro UI Launcher
echo =========================================

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found! Please run installation scripts first.
    pause
    exit /b
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Open the browser (will pause for 2 secs to let server start)
echo [*] Starting Web Server at http://127.0.0.1:5000 ...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000

:: Run the server
python src\web.py

pause
