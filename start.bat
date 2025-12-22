@echo off
REM Wechsle zum Verzeichnis der Batch-Datei
cd /d "%~dp0"

echo YouTube Downloader
echo ==================

REM Prüfe ob yt-dlp installiert ist
python -c "import yt_dlp" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo yt-dlp nicht gefunden, installiere...
    pip install --user -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Fehler bei der Installation!
        echo Bitte fuehren Sie 'pip install --user yt-dlp' manuell aus.
        pause
        exit /b 1
    )
    echo Installation erfolgreich!
)

echo Starte die App...
python youtube_downloader.py