@echo off
setlocal enabledelayedexpansion
echo MediathekManagement-Tool  Backend Server
echo =========================================
echo.

cd /d "%~dp0"
set BACKEND_DIR=%~dp0
set ROOT_DIR=%~dp0..
set VENV_PYTHON=%ROOT_DIR%\.venv\Scripts\python.exe
set VENV_ACTIVATE=%ROOT_DIR%\.venv\Scripts\activate.bat

:: Prefer the project venv if it exists, otherwise fall back to system Python
if exist "%VENV_PYTHON%" (
    echo    Using project virtual environment...
    set USE_PYTHON=%VENV_PYTHON%
) else (
    echo    No virtual environment found, using system Python.
    echo    Tip: Run start.bat from the project root to create one.
    set USE_PYTHON=python
)

echo    Installing/updating dependencies...
"%USE_PYTHON%" -m pip install -r "%BACKEND_DIR%requirements.txt" --quiet

if %ERRORLEVEL% EQU 0 (
    echo.
    echo    Starting server on http://localhost:8000
    echo    API docs available at http://localhost:8000/docs
    echo.
    "%USE_PYTHON%" start_server.py
) else (
    echo.
    echo  !! ERROR: Could not install dependencies.
    pause
)

endlocal
