@echo off
echo Starting MediathekManagement-Tool Desktop Frontend
echo ==================================================
echo.

cd /d "%~dp0"

echo Installing/Updating dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% == 0 (
    echo.
    echo IMPORTANT: Make sure the backend server is running!
    echo Start it with: backend\start_backend.bat
    echo.
    echo Starting desktop application...
    echo.
    python mediathek_desktop.py
) else (
    echo.
    echo Error installing dependencies!
    pause
)
