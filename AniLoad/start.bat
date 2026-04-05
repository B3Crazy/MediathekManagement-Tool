@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"
set "REQ_FILE=%ROOT_DIR%requirements.txt"
set "MAIN_FILE=%ROOT_DIR%AniLoad.py"

echo == AniLoad starter ==

if not exist "%MAIN_FILE%" (
	echo Error: AniLoad.py not found in %ROOT_DIR%
	exit /b 1
)

set "PYTHON_CMD="
where py >nul 2>&1
if %errorlevel%==0 (
	py -3.8 -c "import sys" >nul 2>&1
	if %errorlevel%==0 set "PYTHON_CMD=py -3.8"
)

if "%PYTHON_CMD%"=="" (
	where python >nul 2>&1
	if %errorlevel%==0 (
		python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
		if %errorlevel%==0 set "PYTHON_CMD=python"
	)
)

if "%PYTHON_CMD%"=="" (
	echo Error: Python 3.8+ not found in PATH.
	exit /b 1
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
	echo Creating virtual environment in %VENV_DIR%
	%PYTHON_CMD% -m venv "%VENV_DIR%"
	if errorlevel 1 (
		echo Error: Failed to create virtual environment.
		exit /b 1
	)
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

echo Installing dependencies
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 (
	echo Error: pip upgrade failed.
	exit /b 1
)

for %%I in ("%REQ_FILE%") do set "REQ_SIZE=%%~zI"
if exist "%REQ_FILE%" if not "%REQ_SIZE%"=="0" (
	"%VENV_PYTHON%" -m pip install -r "%REQ_FILE%"
) else (
	rem Fallback when requirements file is still empty.
	"%VENV_PYTHON%" -m pip install aniworld rich
)

if errorlevel 1 (
	echo Error: Dependency installation failed.
	exit /b 1
)

echo Starting AniLoad
cd /d "%ROOT_DIR%"
"%VENV_PYTHON%" "%MAIN_FILE%" %*

exit /b %errorlevel%
