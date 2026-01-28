@echo off
echo ========================================
echo MediathekManagement-Tool - Quick Start
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1/4: Checking and installing dependencies...
echo.
python backend\dependency_checker.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Warning: Some dependencies might be missing!
    echo The application may not work correctly.
    echo.
    pause
)

echo.
echo Step 2/4: Starting backend server...
start "MediathekManagement Backend" cmd /k "cd backend && python start_server.py"

echo.
echo Step 3/4: Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo.
echo Step 4/4: Starting web frontend...
cd frontend
echo Opening web frontend at http://localhost:8080
echo.
start "" "http://localhost:8080"
python -m http.server 8080 --bind 0.0.0.0

echo.
echo Application closed.
pause
