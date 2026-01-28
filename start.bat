@echo off
echo ========================================
echo MediathekManagement-Tool - Quick Start
echo ========================================
echo.
echo This script will start both the backend server
echo and the desktop frontend application.
echo.

cd /d "%~dp0"

echo Step 1/3: Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error installing dependencies!
    pause
    exit /b 1
)

echo.
echo Step 2/3: Starting backend server...
start "MediathekManagement Backend" cmd /k "cd backend && python start_server.py"

echo.
echo Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo.
echo Step 3/3: Starting web frontend...
cd frontend
echo Opening web frontend at http://localhost:8080
echo.
start "" "http://localhost:8080"
python -m http.server 8080 --bind 0.0.0.0

echo.
echo Application closed.
pause
