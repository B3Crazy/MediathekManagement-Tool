@echo off
echo Starting MediathekManagement-Tool Backend Server
echo ================================================
echo.

cd /d "%~dp0"

echo Installing/Updating dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% == 0 (
    echo.
    echo Starting server on http://localhost:8000
    echo API documentation available at http://localhost:8000/docs
    echo.
    python start_server.py
) else (
    echo.
    echo Error installing dependencies!
    pause
)
