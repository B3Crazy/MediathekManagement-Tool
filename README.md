# MediathekManagement-Tool

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

Eine umfassende Desktop-Anwendung zum Herunterladen von YouTube-Videos und -Audio sowie zum Rippen von DVDs zu MKV-Dateien. Die Anwendung bietet eine benutzerfreundliche grafische Oberfläche mit Echtzeit-Fortschrittsanzeige und umfangreichen Konfigurationsmöglichkeiten.

## Inhaltsverzeichnis

- [Funktionsübersicht](#funktionsübersicht)
- [Systemanforderungen](#systemanforderungen)
- [Installation](#installation)
  - [Schnellstart](#schnellstart)
  - [Manuelle Installation](#manuelle-installation)
  - [Externe Abhängigkeiten](#externe-abhängigkeiten)
- [Verwendung](#verwendung)
  - [YouTube-Video-Download](#youtube-video-download)
  - [YouTube-Audio-Download](#youtube-audio-download)
  - [DVD zu MKV](#dvd-zu-mkv)
- [Konfiguration](#konfiguration)
- [Funktionen im Detail](#funktionen-im-detail)
- [Fehlerbehebung](#fehlerbehebung)
- [Häufig gestellte Fragen (FAQ)](#häufig-gestellte-fragen-faq)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Roadmap](#roadmap)
- [Mitwirkende](#mitwirkende)
- [Lizenz](#lizenz)

## Funktionsübersicht

### YouTube-Video-Download
- **Mehrere Videos gleichzeitig**: Erstellen Sie Warteschlangen mit beliebig vielen YouTube-URLs
- **Hohe Qualität**: Automatischer Download in höchstmöglicher Qualität (bis zu 8K, falls verfügbar)
- **Formatwahl**: Unterstützung für MP4 und MKV Container-Formate
- **Intelligente Formatauswahl**: Bevorzugt optimale Video-/Audio-Streams basierend auf Verfügbarkeit
- **Metadata-Einbettung**: Automatisches Einbetten von Thumbnails und Metadaten
- **Fehlertoleranz**: Automatische Wiederholungsversuche (bis zu 10x) bei fehlgeschlagenen Downloads
- **Fortschrittsanzeige**: Echtzeit-Fortschritt sowohl für einzelne Dateien als auch für die gesamte Warteschlange

### YouTube-Audio-Download
- **Audio-Extraktion**: Extrahiert hochwertige Audiospuren von YouTube-Videos
- **Mehrere Formate**: Unterstützung für MP3 und WAV
- **Beste Qualität**: Automatische Auswahl der höchsten verfügbaren Audioqualität
- **Metadata**: Einbettung von Cover-Art, Titel, Künstler und Jahr (außer bei WAV)
- **Intelligente Metadaten**: Automatische Übernahme des YouTube-Kanal-Namens als Artist
- **Detaillierte Fehlerprotokolle**: Separate Logdateien für Audio-Downloads

### DVD zu MKV (nicht funktionell)
- **DVD-Ripping**: Konvertierung von DVD-Titeln zu MKV-Dateien
- **Mehrfachauswahl**: Rippen Sie mehrere Titel gleichzeitig
- **Merge-Funktion**: Kombinieren Sie mehrere Titel in eine einzelne MKV-Datei
- **Titel-Vorschau**: Zeigt Details zu jedem Titel (Länge, Größe) vor dem Ripping
- **MakeMKV-Integration**: Automatische Erkennung oder manuelle Auswahl der MakeMKV-Installation
- **Laufwerkserkennung**: Automatisches Scannen nach verfügbaren DVD-Laufwerken

## Systemanforderungen

### Betriebssystem
- **Windows 7/8/10/11** (64-bit empfohlen)

### Hardware
- **Prozessor**: Dual-Core CPU oder besser
- **Arbeitsspeicher**: Mindestens 2 GB RAM (4 GB empfohlen)
- **Festplattenspeicher**: 
  - 100 MB für die Anwendung
  - Ausreichend Speicherplatz für heruntergeladene Medien (variabel)
- **DVD-Laufwerk**: Erforderlich für DVD-Ripping-Funktion

### Software
- **Python**: Version 3.7 oder höher
- **pip**: Python-Paketmanager (normalerweise mit Python installiert)

### Optionale Komponenten
- **FFmpeg**: Für erweiterte Video-/Audio-Verarbeitung (automatisch erkannt)
- **MakeMKV**: Für DVD-Ripping-Funktionalität
- **MKVToolNix**: Für erweiterte MKV-Merge-Optionen (optional)

## Installation

### Schnellstart

1. **Repository klonen oder herunterladen**:
   ```bash
   git clone https://github.com/B3Crazy/MediathekManagement-Tool.git
   cd MediathekManagement-Tool
   ```

2. **Installation starten**:
   
   Doppelklicken Sie auf `start.bat` oder führen Sie in der Eingabeaufforderung aus:
   ```bash
   start.bat
   ```
   
   Das Skript installiert automatisch alle erforderlichen Python-Abhängigkeiten und startet die Anwendung.

### Manuelle Installation

Falls Sie die manuelle Installation bevorzugen:

1. **Python-Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Anwendung starten**:
   ```bash
   python youtube_downloader.py
   ```

### Externe Abhängigkeiten

#### FFmpeg (empfohlen)

FFmpeg ermöglicht erweiterte Funktionen wie das Zusammenführen von separaten Video- und Audio-Streams (für 4K/8K-Videos).

**Installation**:
1. Laden Sie FFmpeg von [ffmpeg.org](https://ffmpeg.org/download.html) herunter
2. Entpacken Sie das Archiv
3. Fügen Sie den `bin`-Ordner zum System-PATH hinzu
4. Überprüfen Sie die Installation: `ffmpeg -version`

**Alternative**: Chocolatey-Installation
```bash
choco install ffmpeg
```

#### MakeMKV (für DVD-Ripping)

**Installation**:
1. Laden Sie MakeMKV von [makemkv.com](https://www.makemkv.com/download/) herunter
2. Installieren Sie das Programm (Standard-Installationspfad wird automatisch erkannt)
3. Aktivieren Sie die Software mit einem Beta-Key oder einer Lizenz

**Hinweis**: Die Anwendung erkennt MakeMKV automatisch in den Standard-Installationspfaden:
- `C:\Program Files (x86)\MakeMKV\makemkvcon.exe`
- `C:\Program Files\MakeMKV\makemkvcon.exe`

Falls MakeMKV nicht erkannt wird, können Sie den Pfad manuell auswählen.

## Verwendung

### YouTube-Video-Download

1. **Starten Sie die Anwendung** und wechseln Sie zum Tab **"YouTube → Video"**

2. **Format auswählen**:
   - **MP4**: Empfohlen für beste Kompatibilität
   - **MKV**: Unterstützt erweiterte Features und höhere Qualität

3. **Speicherort festlegen**:
   - Klicken Sie auf "Durchsuchen", um den Zielordner auszuwählen
   - Standard: `Downloads`-Ordner des Benutzers

4. **URLs hinzufügen**:
   - Fügen Sie YouTube-URLs in das Eingabefeld ein
   - Klicken Sie auf "Zur Liste hinzufügen"
   - Wiederholen Sie den Vorgang für mehrere Videos
   - Unterstützte URL-Formate:
     - `https://www.youtube.com/watch?v=...`
     - `https://youtu.be/...`
     - `https://m.youtube.com/watch?v=...`

5. **Optional - Formate prüfen**:
   - Wählen Sie eine URL aus der Liste
   - Klicken Sie auf "Formate prüfen", um verfügbare Qualitätsstufen anzuzeigen

6. **Download starten**:
   - Klicken Sie auf "Download starten"
   - Beobachten Sie den Fortschritt in den Fortschrittsbalken:
     - **Oberer Balken**: Gesamtfortschritt aller Videos
     - **Unterer Balken**: Fortschritt der aktuellen Datei

7. **Ergebnis**:
   - Videos werden im ausgewählten Ordner gespeichert
   - Dateiname: Original-YouTube-Titel
   - Bei Fehlern wird eine `video_error.log` erstellt

### YouTube-Audio-Download

1. **Wechseln Sie zum Tab** **"YouTube → Audio"**

2. **Audio-Format wählen**:
   - **MP3**: Komprimiert, kleinere Dateigröße, mit Metadaten
   - **WAV**: Unkomprimiert, höchste Qualität, größere Dateien

3. **Speicherort und URLs hinzufügen** (wie bei Video-Downloads)

4. **Download starten**:
   - Die Anwendung lädt die beste verfügbare Audiospur herunter
   - Bei MP3: Automatische Einbettung von:
     - Cover-Art (Thumbnail)
     - Titel
     - Artist (YouTube-Kanal-Name)
     - Erscheinungsjahr

5. **Fehlerprotokoll**:
   - Bei Problemen wird `audio_error.log` im Zielordner erstellt
   - Enthält detaillierte Informationen zu fehlgeschlagenen Downloads

### DVD zu MKV

1. **Wechseln Sie zum Tab** **"DVD → MKV"**

2. **DVD-Laufwerk scannen**:
   - Legen Sie eine DVD ein
   - Klicken Sie auf "Laufwerke scannen"
   - Das Laufwerk wird automatisch erkannt (sucht nach `VIDEO_TS`-Ordner)

3. **Ausgabeordner wählen**:
   - Standard: `Videos`-Ordner des Benutzers
   - Klicken Sie auf "Durchsuchen" zum Ändern

4. **Titel laden**:
   - Klicken Sie auf "Titel laden"
   - Die Anwendung liest alle verfügbaren DVD-Titel mit Details:
     - Titel-Nummer
     - Name
     - Länge
     - Dateigröße

5. **Titel auswählen**:
   - Klicken Sie auf die Checkbox in der ersten Spalte zum Auswählen
   - Oder: Markieren Sie Zeilen mit Maus/Tastatur

6. **Ripping-Optionen**:
   - **"Ausgewählte rippen"**: Jeder Titel wird als separate MKV-Datei gespeichert
   - **"In 1 MKV rippen"**: Alle ausgewählten Titel werden zu einer Datei zusammengeführt
     - Erfordert: MKVToolNix (mkvmerge) oder FFmpeg

7. **Fortschritt**:
   - Der Status wird am unteren Rand des Tabs angezeigt
   - Ripping kann je nach DVD-Größe mehrere Minuten dauern

## Konfiguration

### Format-Strings und Qualität

Die Anwendung verwendet intelligente Format-Strings für optimale Qualität:

**Mit FFmpeg** (ermöglicht 4K/8K):
- **MP4**: Bevorzugt MP4-Streams, fällt auf beste Qualität zurück
- **MKV**: Lädt höchstmögliche Qualität (4K/8K wenn verfügbar)

**Ohne FFmpeg**:
- Nur progressive Downloads (Video+Audio in einer Datei)
- Mindestens 720p, wenn verfügbar

### Cache-Verzeichnis

- YouTube-Downloads verwenden ein temporäres Cache-Verzeichnis
- Pfad: `%TEMP%\yt-dlp-cache`
- Wird automatisch erstellt und verwaltet
- Speichert Thumbnails und temporäre Daten

### Wiederholungsversuche

Bei fehlgeschlagenen Downloads:
- **Automatische Wiederholungen**: Bis zu 10 Versuche pro Video/Audio
- **Wartezeit**: 2 Sekunden zwischen Versuchen
- **Timeout**: 30 Minuten pro Download
- **Detaillierte Logs**: Die letzten 5-10 Fehlerzeilen werden protokolliert

## Funktionen im Detail

### Intelligente URL-Verarbeitung

- **Duplikat-Erkennung**: Verhindert mehrfaches Hinzufügen derselben URL
- **Timeskip-Entfernung**: Entfernt automatisch `&t=` und `?t=` Parameter
- **URL-Validierung**: Prüft auf gültige YouTube-Domains

### Thumbnail und Metadata

**Video-Downloads**:
- Thumbnails werden in die Video-Datei eingebettet (MP4/MKV)
- Metadaten umfassen: Titel, Uploader, Upload-Datum, Beschreibung

**Audio-Downloads (MP3)**:
- Cover-Art: Höchstauflösendes YouTube-Thumbnail
- Artist: YouTube-Kanal-Name (ohne @-Präfix)
- Titel: Original-Video-Titel
- Jahr: Upload-Jahr
- Album: Optional (nicht standardmäßig gesetzt)

**Audio-Downloads (WAV)**:
- Keine Metadata-Einbettung (WAV unterstützt keine Tags)
- Thumbnail-Dateien werden automatisch entfernt

### Fortschrittsanzeige

Die Anwendung bietet mehrere Fortschrittsebenen:

1. **Gesamt-Fortschritt**: Zeigt, wie viele Videos/Audios bereits verarbeitet wurden
2. **Datei-Fortschritt**: Zeigt den Download-Fortschritt der aktuellen Datei
3. **Status-Labels**: Textuelle Beschreibung des aktuellen Schritts:
   - "Download: X%"
   - "Extrahiere Audio..."
   - "Bette Thumbnail ein..."
   - "Bette Metadaten ein..."

### DVD-Funktionalität

**Titel-Analyse**:
- Nutzt MakeMKV zur Extraktion von Titel-Informationen
- Zeigt Länge in HH:MM:SS-Format
- Zeigt Dateigröße in MiB

**Ripping-Modi**:
1. **Einzeln**: Jeder Titel → separate MKV-Datei
2. **Zusammengeführt**: Mehrere Titel → eine MKV-Datei
   - Bevorzugt: `mkvmerge` (MKVToolNix)
   - Fallback: `ffmpeg` mit concat-Demuxer

**Laufwerkserkennung**:
- Scannt Laufwerksbuchstaben D: bis Z:
- Prüft auf Vorhandensein des `VIDEO_TS`-Ordners
- Automatische Disc-Index-Ermittlung

## Fehlerbehebung

### yt-dlp nicht gefunden

**Problem**: Fehlermeldung beim Start oder Download

**Lösung**:
1. Die Anwendung bietet automatische Installation an
2. Manuelle Installation: `pip install -U yt-dlp`
3. Überprüfung: `yt-dlp --version`

### FFmpeg nicht erkannt

**Problem**: Nur niedrige Qualität oder keine 4K/8K-Downloads

**Lösung**:
1. FFmpeg installieren (siehe [Externe Abhängigkeiten](#externe-abhängigkeiten))
2. Überprüfen Sie den PATH: `ffmpeg -version`
3. Starten Sie die Anwendung neu

### MakeMKV nicht gefunden

**Problem**: DVD-Tab zeigt Fehler beim Laden von Titeln

**Lösung**:
1. MakeMKV installieren
2. Die Anwendung fordert zur manuellen Auswahl von `makemkvcon.exe` auf
3. Pfad speichern für zukünftige Verwendung

### Download schlägt wiederholt fehl

**Problem**: Download bricht nach 10 Versuchen ab

**Mögliche Ursachen und Lösungen**:
1. **Netzwerkprobleme**:
   - Überprüfen Sie Ihre Internetverbindung
   - Versuchen Sie es später erneut
   
2. **Video nicht verfügbar**:
   - Prüfen Sie, ob das Video noch auf YouTube existiert
   - Prüfen Sie regionale Beschränkungen
   
3. **yt-dlp veraltet**:
   ```bash
   pip install -U yt-dlp
   ```

4. **Fehlerprotokoll prüfen**:
   - Öffnen Sie `video_error.log` oder `audio_error.log`
   - Suchen Sie nach spezifischen Fehlermeldungen

### Thumbnail-Einbettung schlägt fehl

**Problem**: Videos/Audios haben kein eingebettetes Cover

**Lösung**:
- Stellen Sie sicher, dass FFmpeg installiert ist
- Bei Audio: WAV unterstützt keine Thumbnails (verwenden Sie MP3)

### DVD-Merge funktioniert nicht

**Problem**: "In 1 MKV rippen" schlägt fehl

**Lösung**:
1. Installieren Sie MKVToolNix: [mkvtoolnix.download](https://mkvtoolnix.download/)
2. Oder stellen Sie sicher, dass FFmpeg verfügbar ist
3. Überprüfen Sie die Fehlerausgabe für Details

## Häufig gestellte Fragen (FAQ)

### Welche maximale Videoqualität wird unterstützt?

Mit FFmpeg: Bis zu 8K (7680p), falls vom Video unterstützt
Ohne FFmpeg: Maximal die höchste verfügbare progressive Qualität (oft 1080p)

### Kann ich Playlists herunterladen?

Aktuell: Nein. Die Anwendung nutzt `--no-playlist` und lädt nur einzelne Videos.
Workaround: Fügen Sie jede Video-URL einzeln hinzu.

### Werden Untertitel heruntergeladen?

Nein. Untertitel werden bewusst nicht heruntergeladen, um Dateigröße und Komplexität zu reduzieren.

### Kann ich Downloads pausieren?

Nicht direkt. Sie können die Anwendung schließen (Warnung erscheint) und später neu starten. Bereits heruntergeladene Videos bleiben erhalten.

### Wo werden Fehlerprotokolle gespeichert?

- Video: `video_error.log` im Video-Zielordner
- Audio: `audio_error.log` im Audio-Zielordner
- Protokolle werden bei jedem neuen Download-Durchlauf zurückgesetzt

### Wie funktioniert die Artist-Extraktion bei Audio?

Die Anwendung nutzt den YouTube-Kanal-Namen (nicht den Handle):
- `--parse-metadata "%(channel,uploader)s:%(meta_artist)s"`
- Entfernt automatisch führende `@`-Zeichen

### Warum haben WAV-Dateien keine Metadaten?

WAV ist ein PCM-basiertes Format ohne Standard-Metadata-Container. Für Metadaten verwenden Sie MP3 oder M4A.

## Bekannte Einschränkungen

1. **Playlists**: Keine native Playlist-Unterstützung
2. **Untertitel**: Werden nicht heruntergeladen
3. **Live-Streams**: Möglicherweise nicht vollständig unterstützt
4. **Sehr lange Videos**: Können Timeouts verursachen (30-Minuten-Limit)
5. **DRM-geschützte Inhalte**: Nicht unterstützt (YouTube Premium-exklusive Inhalte)
6. **WAV-Metadaten**: Technisch nicht möglich

## Roadmap

Geplante Features für zukünftige Versionen:

- [ ] Playlist-Unterstützung
- [ ] Untertitel-Download (optional)
- [ ] Download-Warteschlangen-Speicherung/Laden
- [ ] Automatische Qualitätsauswahl (z.B. "immer 1080p")
- [ ] Download-Geschwindigkeitsanzeige
- [ ] Parallel-Downloads
- [ ] Integration mit mehr Audio-Formaten (FLAC, OPUS)
- [ ] Kommandozeilen-Modus
- [ ] Portable Version (keine Installation erforderlich)
- [ ] Übersetzungen (Englisch, weitere Sprachen)

## Mitwirkende

Beiträge sind willkommen! 

### So können Sie beitragen:

1. **Forken Sie das Repository**
2. **Erstellen Sie einen Feature-Branch**: `git checkout -b feature/NeuesFunktion`
3. **Committen Sie Ihre Änderungen**: `git commit -am 'Füge neue Funktion hinzu'`
4. **Pushen Sie den Branch**: `git push origin feature/NeuesFunktion`
5. **Erstellen Sie einen Pull Request**

### Richtlinien:
- Folgen Sie PEP 8-Stil für Python-Code
- Fügen Sie Docstrings für neue Funktionen hinzu
- Testen Sie Ihre Änderungen gründlich
- Aktualisieren Sie die README bei Bedarf

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.

---

**Hinweis**: Diese Software dient ausschließlich zu privaten, nicht-kommerziellen Zwecken. Beachten Sie die Nutzungsbedingungen von YouTube und respektieren Sie Urheberrechte. Der Download von urheberrechtlich geschützten Inhalten ohne Erlaubnis ist illegal.

**Entwickelt mit ❤️ für die Community**

Wenn Ihnen dieses Projekt gefällt, geben Sie ihm einen ⭐ auf GitHub!