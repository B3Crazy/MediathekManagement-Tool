@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  MediathekManagement-Tool  Quick Start
echo ========================================
echo.

cd /d "%~dp0"
set "ROOT=%~dp0"
set "VENV_DIR=%ROOT%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

:: ============================================================
:: STEP 1  Find a working Python interpreter
:: ============================================================
echo [1/5] Checking Python installation...

set "PYTHON_CMD="

:: Check 'python' - but skip the Windows Store stub (returns exit 9009)
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        python -c "import sys; exit(0 if sys.version_info>=(3,0) else 1)" >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "PYTHON_CMD=python"
        )
    )
)

:: Try the py launcher if 'python' didn't work
if not defined PYTHON_CMD (
    where py >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        py --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "PYTHON_CMD=py"
        )
    )
)

:: Auto-install via winget if still not found
if not defined PYTHON_CMD (
    echo    Python not found. Attempting automatic installation via winget...
    where winget >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo  !! winget not available. Cannot auto-install Python.
        echo  Please install Python 3.8+ from: https://www.python.org/downloads/
        echo  Enable "Add Python to PATH" during setup, then re-run this script.
        echo.
        powershell -NoProfile -Command "Start-Process 'https://www.python.org/downloads/'" >nul 2>&1
        pause
        exit /b 1
    )
    echo    Running: winget install Python.Python.3.12 ...
    winget install --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    if !ERRORLEVEL! NEQ 0 (
        echo    Trying Python.Python.3.11 as fallback...
        winget install --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements --silent
    )
    :: Refresh PATH from registry so the new Python is visible in this session
    for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('PATH','Machine')+';'+[System.Environment]::GetEnvironmentVariable('PATH','User')"`) do set "PATH=%%P"
    where python >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PYTHON_CMD=python"
    ) else (
        where py >nul 2>&1
        if !ERRORLEVEL! EQU 0 set "PYTHON_CMD=py"
    )
)

if not defined PYTHON_CMD (
    echo.
    echo  !! Python could not be found or installed automatically.
    echo  Please install Python 3.8+ from: https://www.python.org/downloads/
    echo  Enable "Add Python to PATH", then re-run this script.
    echo.
    pause
    exit /b 1
)

:: Version check
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  !! Python version is too old. 3.8 or newer required.
    echo  Please update from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('%PYTHON_CMD% --version 2^>^&1') do echo    Found: %%V

:: ============================================================
:: STEP 2  Create virtual environment
:: ============================================================
echo.
echo [2/5] Setting up virtual environment (.venv)...

if not exist "%VENV_PYTHON%" (
    echo    Creating .venv ...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if !ERRORLEVEL! NEQ 0 (
        echo.
        echo  !! Could not create virtual environment.
        pause
        exit /b 1
    )
    echo    Done.
) else (
    echo    Already exists.
)

:: ============================================================
:: STEP 3  Install dependencies into venv
:: ============================================================
echo.
echo [3/5] Installing Python dependencies...

"%VENV_PYTHON%" -m pip install --upgrade pip --quiet
"%VENV_PYTHON%" -m pip install -r "%ROOT%requirements.txt"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  !! Some packages failed to install. The app may not work correctly.
    pause
) else (
    echo    All dependencies installed.
)

:: ============================================================
:: STEP 4  Check / auto-install ffmpeg
:: ============================================================
echo.
echo [4/5] Checking ffmpeg...

where ffmpeg >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo    ffmpeg found.
) else (
    echo    ffmpeg not found. Trying winget...
    where winget >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        winget install --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements --silent
        for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('PATH','Machine')+';'+[System.Environment]::GetEnvironmentVariable('PATH','User')"`) do set "PATH=%%P"
        where ffmpeg >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo    ffmpeg installed.
        ) else (
            echo    WARNING: ffmpeg still not available. Video downloads may fail.
        )
    ) else (
        echo    WARNING: winget not available. Install ffmpeg manually from https://www.gyan.dev/ffmpeg/builds/
    )
)

:: ============================================================
:: STEP 5  Launch application
:: ============================================================
echo.
echo [5/5] Starting application...
echo.

set "ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "BACKEND=%ROOT%backend"
start "MediathekManagement Backend" cmd /k "call ""%ACTIVATE%"" && cd /d ""%BACKEND%"" && python start_server.py"

echo    Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

echo    Opening web frontend at http://localhost:8080
start "" "http://localhost:8080"

cd /d "%ROOT%frontend"
echo    Frontend server running. Close this window to stop.
echo.
"%VENV_PYTHON%" -m http.server 8080 --bind 0.0.0.0

echo.
echo    Application stopped.
endlocal
pause
