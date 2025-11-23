@echo off
echo YouTube Downloader - Setup
echo ========================

echo Installiere Abhaengigkeiten...
pip install -r requirements.txt

if %ERRORLEVEL% == 0 (
    echo.
    echo Installation erfolgreich!
    echo.
    echo Starte die App...
    python youtube_downloader.py
) else (
    echo.
    echo Fehler bei der Installation!
    echo Bitte führen Sie 'pip install yt-dlp' manuell aus.
    pause
)
