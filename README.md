# YouTube Video Downloader + DVD → MKV

Eine einfache GUI-Anwendung mit zwei Oberflächen (Tabs):
- YouTube-Downloader in höchster Qualität
- DVD → MKV (ähnlich MakeMKV) zum Rippen von DVD-Titeln

## Features

- **Formatwahl**: MP4 oder MKV
- **Speicherort-Auswahl**: Freie Wahl des Download-Ordners
- **URL-Liste**: Mehrere YouTube-Links sammeln und auf einmal downloaden
- **Progressbar**: Anzeige des Download-Fortschritts
- **Höchste Qualität**: Automatische Auswahl der besten verfügbaren Qualität (bis zu 8K/4K)
- **Benutzerfreundlich**: Übersichtliche und funktionelle Oberfläche
- **Zweite Oberfläche: DVD → MKV**
   - DVD-Laufwerk erkennen (Windows)
   - Titel/Sektionen inkl. Titelname, Länge und Größe anzeigen
   - Auswahl mehrerer Titel und Rippen zu MKV (mit MakeMKV CLI)

## Installation

### Voraussetzungen

- Python 3.7 oder höher
- pip (Python Package Installer)
- Für DVD → MKV: Installierte MakeMKV-CLI (makemkvcon) im PATH

### Schritt 1: Abhängigkeiten installieren

Öffnen Sie PowerShell/Kommandozeile im Projektordner und führen Sie aus:

```powershell
pip install -r requirements.txt
```

### Schritt 2: App starten

```powershell
python youtube_downloader.py
```

## Verwendung

1. **Format wählen**: Wählen Sie zwischen MP4 und MKV
2. **Speicherort festlegen**: Klicken Sie auf "Durchsuchen" um den Download-Ordner zu wählen
3. **URLs hinzufügen**: 
   - YouTube-URL in das Textfeld eingeben
   - Auf "Zur Liste hinzufügen" klicken
   - Wiederholen für weitere Videos
4. **Download starten**: Klicken Sie auf "Download starten"

### Tab: DVD → MKV
1. Stellen Sie sicher, dass MakeMKV installiert ist und `makemkvcon` im PATH liegt.
2. Wechseln Sie zum Tab "DVD → MKV".
3. Klicken Sie auf "Laufwerke scannen" und wählen Sie Ihr DVD-Laufwerk aus.
4. Klicken Sie auf "Titel laden", um verfügbare Titel/Sektionen zu laden.
5. Markieren Sie die gewünschten Titel in der Liste (Mehrfachauswahl möglich).
6. Wählen Sie einen Ausgabeordner.
7. Klicken Sie auf "Ausgewählte rippen", um MKV-Dateien zu erzeugen.

## Automatische Installation von yt-dlp

Falls `yt-dlp` nicht installiert ist, bietet die App eine automatische Installation an.

## MakeMKV / DVD-Hinweise

- Für Rippen wird die MakeMKV-CLI benötigt: https://www.makemkv.com/
- Unter Windows heißt das Tool `makemkvcon.exe` und sollte im PATH verfügbar sein.
- Die Laufwerkserkennung prüft Windows-Laufwerke D:..Z: auf ein `VIDEO_TS`-Verzeichnis.

## Unterstützte URLs

- https://www.youtube.com/watch?v=...
- https://youtu.be/...
- https://m.youtube.com/...

## Technische Details

- **GUI Framework**: tkinter (in Python integriert)
- **Download Engine**: yt-dlp (modernste YouTube-Download-Bibliothek)
- **Threading**: Downloads laufen in separaten Threads ohne UI-Blockierung
- **Qualität**: Automatische Auswahl der höchsten verfügbaren Qualität
- **DVD → MKV**: MakeMKV CLI (`makemkvcon`) zum Auflisten (info) und Rippen (mkv) von Titeln

## Fehlerbehebung

### "yt-dlp nicht gefunden"
- Stellen Sie sicher, dass Python und pip installiert sind
- Führen Sie `pip install yt-dlp` manuell aus

### "Fehler beim Download"
- Überprüfen Sie die Internetverbindung
- Stellen Sie sicher, dass die YouTube-URL korrekt ist
- Manche Videos können regionsspezifisch blockiert sein

### Langsame Downloads
- Die Download-Geschwindigkeit hängt von Ihrer Internetverbindung ab
- Sehr hohe Qualitäten (4K/8K) sind größer und brauchen länger

## Lizenz

Dieses Projekt ist für den persönlichen Gebrauch bestimmt. Beachten Sie die YouTube-Nutzungsbedingungen beim Herunterladen von Videos.
