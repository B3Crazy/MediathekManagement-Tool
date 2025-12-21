#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Video Downloader App
Einfache GUI zum Sammeln von YouTube-Links, Formatwahl (MP4/MKV), Zielordner,
Fortschrittsanzeige und Download in höchster Qualität.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import time
import tempfile
from pathlib import Path
import queue
import subprocess
import logging
import re
import csv


class YouTubeDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # State
        self.download_format = tk.StringVar(value="mp4")
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_links = []
        self.is_downloading = False
        self.ffmpeg_available = False

        # Audio tab states
        self.audio_format = tk.StringVar(value="mp3")
        self.audio_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.audio_links = []
        self.is_downloading_audio = False

        # Queues/state
        self.progress_queue = queue.Queue()

        # Logger-Konfiguration (einmalig im Projektverzeichnis)
        self.setup_logger()
        
        # CSV-Datei für fehlgeschlagene Downloads initialisieren
        self.failed_downloads_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging\\failed_downloads.csv")
        self.clear_failed_downloads_csv()
        
        self.logger("info", "Anwendung gestartet")

        # Build UI (two tabs)
        self.create_widgets()

        # Tooling checks
        self.check_ytdlp()
        self.ffmpeg_available = self.check_ffmpeg()

        # Queue pump
        self.check_progress_queue()

    # ---------------------- UI ----------------------
    def create_widgets(self):
        main = ttk.Frame(self.root, padding=0)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Tabs
        self.tabs = ttk.Notebook(main)
        self.tabs.grid(row=0, column=0, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)

        # Tab 1: YouTube Video
        tab_yt = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_yt, text="YouTube → Video")

        # Tab 2: YouTube Audio
        tab_audio = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_audio, text="YouTube → Audio")

        # ----- Tab YouTube UI -----
        lf_format = ttk.LabelFrame(tab_yt, text="Video Format", padding=8)
        lf_format.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Radiobutton(lf_format, text="MP4", variable=self.download_format, value="mp4").grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(lf_format, text="MKV", variable=self.download_format, value="mkv").grid(row=0, column=1)

        # Zielordner
        lf_path = ttk.LabelFrame(tab_yt, text="Speicherort", padding=8)
        lf_path.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_path.columnconfigure(0, weight=1)
        self.path_entry = ttk.Entry(lf_path, textvariable=self.download_path, state="readonly")
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(lf_path, text="Durchsuchen", command=self.browse_folder).grid(row=0, column=1)

        # URL-Eingabe
        lf_url = ttk.LabelFrame(tab_yt, text="YouTube URL hinzufügen", padding=8)
        lf_url.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_url.columnconfigure(0, weight=1)
        self.url_entry = ttk.Entry(lf_url)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.url_placeholder = "https://www.youtube.com/watch?v=..."
        self.url_entry.insert(0, self.url_placeholder)
        self.url_entry.config(foreground="grey")
        self.url_entry.bind("<FocusIn>", self.on_url_entry_focus_in)
        self.url_entry.bind("<FocusOut>", self.on_url_entry_focus_out)
        ttk.Button(lf_url, text="Zur Liste hinzufügen", command=self.add_url_to_list).grid(row=0, column=1)

        # URL-Liste
        lf_list = ttk.LabelFrame(tab_yt, text="Download-Liste", padding=8)
        lf_list.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        lf_list.rowconfigure(0, weight=1)
        lf_list.columnconfigure(0, weight=1)
        list_container = ttk.Frame(lf_list)
        list_container.grid(row=0, column=0, sticky="nsew")
        list_container.rowconfigure(0, weight=1)
        list_container.columnconfigure(0, weight=1)
        self.url_listbox = tk.Listbox(list_container, height=10)
        self.url_listbox.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(list_container, orient="vertical", command=self.url_listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.url_listbox.config(yscrollcommand=sb.set)

        btns = ttk.Frame(lf_list)
        btns.grid(row=1, column=0, pady=(8, 0))
        ttk.Button(btns, text="Ausgewählte entfernen", command=self.remove_selected_url).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Liste leeren", command=self.clear_url_list).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btns, text="Formate prüfen", command=self.check_formats).pack(side=tk.LEFT)

        # Progress
        lf_prog = ttk.LabelFrame(tab_yt, text="Download-Status", padding=8)
        lf_prog.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_prog.columnconfigure(0, weight=1)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(lf_prog, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.status_label = ttk.Label(lf_prog, text="Bereit zum Download")
        self.status_label.grid(row=1, column=0, sticky="w")
        # Current file progress
        self.current_progress_var = tk.DoubleVar(value=0)
        self.current_progress_bar = ttk.Progressbar(lf_prog, variable=self.current_progress_var, maximum=100)
        self.current_progress_bar.grid(row=2, column=0, sticky="ew", pady=(6, 6))
        self.current_status_label = ttk.Label(lf_prog, text="")
        self.current_status_label.grid(row=3, column=0, sticky="w")

        # Start
        self.download_button = ttk.Button(tab_yt, text="Download starten", command=self.start_download)
        self.download_button.grid(row=5, column=0, columnspan=2)

        # Layout stretch
        tab_yt.rowconfigure(3, weight=1)
        tab_yt.columnconfigure(0, weight=1)

        # ----- Tab Audio UI -----
        # Audio Format Auswahl
        lf_audio_format = ttk.LabelFrame(tab_audio, text="Audio Format", padding=8)
        lf_audio_format.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Radiobutton(lf_audio_format, text="MP3", variable=self.audio_format, value="mp3").grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(lf_audio_format, text="WAV", variable=self.audio_format, value="wav").grid(row=0, column=1)

        # Zielordner
        lf_audio_path = ttk.LabelFrame(tab_audio, text="Speicherort", padding=8)
        lf_audio_path.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_audio_path.columnconfigure(0, weight=1)
        self.audio_path_entry = ttk.Entry(lf_audio_path, textvariable=self.audio_path, state="readonly")
        self.audio_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(lf_audio_path, text="Durchsuchen", command=self.browse_audio_folder).grid(row=0, column=1)

        # URL-Eingabe
        lf_audio_url = ttk.LabelFrame(tab_audio, text="YouTube URL hinzufügen", padding=8)
        lf_audio_url.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_audio_url.columnconfigure(0, weight=1)
        self.audio_url_entry = ttk.Entry(lf_audio_url)
        self.audio_url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.audio_url_placeholder = "https://www.youtube.com/watch?v=..."
        self.audio_url_entry.insert(0, self.audio_url_placeholder)
        self.audio_url_entry.config(foreground="grey")
        self.audio_url_entry.bind("<FocusIn>", self.on_audio_url_entry_focus_in)
        self.audio_url_entry.bind("<FocusOut>", self.on_audio_url_entry_focus_out)
        ttk.Button(lf_audio_url, text="Zur Liste hinzufügen", command=self.add_audio_url_to_list).grid(row=0, column=1)

        # URL-Liste
        lf_audio_list = ttk.LabelFrame(tab_audio, text="Download-Liste", padding=8)
        lf_audio_list.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        lf_audio_list.rowconfigure(0, weight=1)
        lf_audio_list.columnconfigure(0, weight=1)
        audio_list_container = ttk.Frame(lf_audio_list)
        audio_list_container.grid(row=0, column=0, sticky="nsew")
        audio_list_container.rowconfigure(0, weight=1)
        audio_list_container.columnconfigure(0, weight=1)
        self.audio_url_listbox = tk.Listbox(audio_list_container, height=10)
        self.audio_url_listbox.grid(row=0, column=0, sticky="nsew")
        sb_audio = ttk.Scrollbar(audio_list_container, orient="vertical", command=self.audio_url_listbox.yview)
        sb_audio.grid(row=0, column=1, sticky="ns")
        self.audio_url_listbox.config(yscrollcommand=sb_audio.set)

        audio_btns = ttk.Frame(lf_audio_list)
        audio_btns.grid(row=1, column=0, pady=(8, 0))
        ttk.Button(audio_btns, text="Ausgewählte entfernen", command=self.remove_selected_audio_url).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(audio_btns, text="Liste leeren", command=self.clear_audio_url_list).pack(side=tk.LEFT)

        # Progress
        lf_audio_prog = ttk.LabelFrame(tab_audio, text="Download-Status", padding=8)
        lf_audio_prog.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_audio_prog.columnconfigure(0, weight=1)
        self.audio_progress_var = tk.DoubleVar(value=0)
        self.audio_progress_bar = ttk.Progressbar(lf_audio_prog, variable=self.audio_progress_var, maximum=100)
        self.audio_progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.audio_status_label = ttk.Label(lf_audio_prog, text="Bereit zum Download")
        self.audio_status_label.grid(row=1, column=0, sticky="w")
        # Current file progress
        self.audio_current_progress_var = tk.DoubleVar(value=0)
        self.audio_current_progress_bar = ttk.Progressbar(lf_audio_prog, variable=self.audio_current_progress_var, maximum=100)
        self.audio_current_progress_bar.grid(row=2, column=0, sticky="ew", pady=(6, 6))
        self.audio_current_status_label = ttk.Label(lf_audio_prog, text="")
        self.audio_current_status_label.grid(row=3, column=0, sticky="w")

        # Start
        self.audio_download_button = ttk.Button(tab_audio, text="Download starten", command=self.start_audio_download)
        self.audio_download_button.grid(row=5, column=0, columnspan=2)

        # Layout stretch
        tab_audio.rowconfigure(3, weight=1)
        tab_audio.columnconfigure(0, weight=1)

    def on_url_entry_focus_in(self, _):
        if self.url_entry.get() == self.url_placeholder:
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(foreground="black")

    def on_url_entry_focus_out(self, _):
        if not self.url_entry.get().strip():
            self.url_entry.insert(0, self.url_placeholder)
            self.url_entry.config(foreground="grey")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            self.logger("info", f"Video-Speicherort geändert: {folder}")

    def add_url_to_list(self):
        url = self.url_entry.get().strip()
        if not url or url == self.url_placeholder:
            messagebox.showwarning("Warnung", "Bitte geben Sie eine URL ein.")
            return
        if not (url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://m.youtube.com/")):
            messagebox.showwarning("Warnung", "Bitte geben Sie eine gültige YouTube-URL ein.")
            return
        
        # Entferne Timeskip-Parameter (&t=... oder ?t=...)
        url = re.sub(r'[&?]t=\d+[smh]?', '', url)
        
        if url in self.url_links:
            messagebox.showinfo("Info", "Diese URL ist bereits in der Liste.")
            self.logger("info", f"Versuch, doppelte URL hinzuzufügen: {url}")
            return
        self.url_links.append(url)
        self.url_listbox.insert(tk.END, url)
        self.url_entry.delete(0, tk.END)
        self.on_url_entry_focus_out(None)
        self.logger("info", f"Video-URL zur Liste hinzugefügt: {url}")

    def remove_selected_url(self):
        sel = self.url_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Bitte wählen Sie eine URL aus der Liste aus.")
            return
        idx = sel[0]
        removed_url = self.url_links[idx]
        self.url_listbox.delete(idx)
        del self.url_links[idx]
        self.logger("info", f"Video-URL aus Liste entfernt: {removed_url}")

    def clear_url_list(self):
        if not self.url_links:
            return
        if messagebox.askyesno("Liste leeren", "Möchten Sie alle URLs aus der Liste entfernen?"):
            count = len(self.url_links)
            self.url_links.clear()
            self.url_listbox.delete(0, tk.END)
            self.logger("info", f"Video-Liste geleert ({count} URLs entfernt)")

    # ---------------------- Tools ----------------------
    def setup_logger(self):
        """Einmalige Konfiguration des Loggers im Projektverzeichnis"""
        project_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(project_dir, "logging\\youtube_downloader.log")
        
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            force=True
        )
    
    def logger(self, severity, message: str):
        """Loggt Nachrichten mit entsprechendem Schweregrad"""
        if severity == "info":
            logging.info(message)
        elif severity == "warning":
            logging.warning(message)
        elif severity == "error":
            logging.error(message)
        else:
            logging.debug(message)
    
    def clear_failed_downloads_csv(self):
        """Fügt einen Session-Trenner zur CSV-Datei hinzu"""
        try:
            # Prüfe ob Datei existiert, wenn nicht, erstelle Header
            if not os.path.exists(self.failed_downloads_csv):
                with open(self.failed_downloads_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['URL', 'Typ', 'Zeitstempel'])
                self.logger("info", "CSV-Datei für fehlgeschlagene Downloads erstellt")
            else:
                # Füge Session-Trenner hinzu
                with open(self.failed_downloads_csv, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['---', '---', '---'])
                self.logger("info", "Session-Trenner zur CSV-Datei hinzugefügt")
        except Exception as e:
            self.logger("error", f"Fehler beim Bearbeiten der CSV-Datei: {e}")
    
    def add_failed_download_to_csv(self, url: str, download_type: str, error_details: str = ""):
        """Fügt einen fehlgeschlagenen Download zur CSV-Datei hinzu"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.failed_downloads_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([url, download_type, timestamp])
            self.logger("info", f"Fehlgeschlagener {download_type}-Download zur CSV hinzugefügt: {url}")
        except Exception as e:
            self.logger("error", f"Fehler beim Schreiben in CSV-Datei: {e}")
    
    def check_ytdlp(self) -> bool:
        try:
            r = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        # Install attempt
        if messagebox.askyesno("yt-dlp nicht gefunden", "yt-dlp ist nicht installiert. Jetzt installieren?"):
            self.status_label.config(text="Installiere yt-dlp...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()

            def _install():
                try:
                    r = subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], capture_output=True, text=True, timeout=300)
                    ok = r.returncode == 0
                    self.progress_queue.put(("install_complete", ok, r.stderr if not ok else ""))
                except Exception as e:
                    self.progress_queue.put(("install_complete", False, str(e)))
            threading.Thread(target=_install, daemon=True).start()
            return False
        return False

    def check_ffmpeg(self) -> bool:
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    # ---------------------- Downloads ----------------------
    def start_download(self):
        if self.is_downloading:
            messagebox.showinfo("Info", "Download läuft bereits.")
            return
        if not self.url_links:
            messagebox.showwarning("Warnung", "Bitte fügen Sie mindestens eine URL hinzu.")
            return
        if not os.path.isdir(self.download_path.get()):
            messagebox.showerror("Fehler", "Der gewählte Speicherort existiert nicht.")
            self.logger("error", "Der gewählte Speicherort existiert nicht.")
            return

        # Warnung wenn MKV ohne ffmpeg
        if self.download_format.get() == "mkv" and not self.ffmpeg_available:
            if not messagebox.askyesno(
                "ffmpeg nicht verfügbar",
                "MKV-Downloads funktionieren am besten mit ffmpeg.\n\n"
                "Ohne ffmpeg sind nur niedrigere Auflösungen verfügbar und das Ergebnis könnte "
                "als WebM statt MKV gespeichert werden.\n\n"
                "Möchten Sie trotzdem fortfahren?"
            ):
                self.logger("info", "Video-Download abgebrochen (MKV ohne ffmpeg)")
                return

        self.is_downloading = True
        self.download_button.config(text="Download läuft...", state="disabled")
        self.progress_var.set(0)
        self.logger("info", f"Video-Download gestartet: {len(self.url_links)} URLs, Format: {self.download_format.get()}, Ziel: {self.download_path.get()}")
        threading.Thread(target=self.download_videos, daemon=True).start()

    def select_format_string(self) -> str:
        # Mit ffmpeg: getrennte Streams (4K/8K) möglich
        if self.ffmpeg_available:
            # Beide Formate verwenden die gleiche kompatible Stream-Auswahl
            # Der Unterschied liegt nur im Container-Format (--merge-output-format)
            return (
                "bv*[height>=4320][ext=mp4]+ba[ext=m4a]/"
                "bv*[height>=2160][ext=mp4]+ba[ext=m4a]/"
                "bv*[height>=1080][ext=mp4]+ba[ext=m4a]/"
                "bv*+ba/b"
            )
        else:
            # Ohne ffmpeg: Nur progressive Downloads möglich
            # Warnung: Höhere Auflösungen (4K/8K) erfordern ffmpeg
            if self.download_format.get() == "mp4":
                return "b[ext=mp4][height>=720]/b[ext=mp4]/b"
            else:
                # MKV ohne ffmpeg: Verwende beste verfügbare progressive Formate
                return "b[height>=720]/b"

    def download_videos(self):
        # Cache-Ordner für yt-dlp im TEMP-Verzeichnis erstellen (für Thumbnails)
        # Nutze direkt TEMP statt verstecktes .cache Verzeichnis (Windows-kompatibel)
        cache_dir = os.path.join(tempfile.gettempdir(), "yt-dlp-cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        total = len(self.url_links)
        max_retries = 10
        
        # Starte Downloads
        for idx, url in enumerate(self.url_links):
            progress = (idx / total) * 100 if total else 0
            self.progress_queue.put(("progress", progress, f"Starte Download {idx+1} von {total}..."))
            self.progress_queue.put(("current_progress", 0, ""))
            
            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    self.progress_queue.put(("current_progress", 0, f"Versuch {attempt}/{max_retries} für Video {idx+1}"))

                    fmt = self.select_format_string()
                    out = os.path.join(self.download_path.get(), "%(title)s.%(ext)s")
                    cmd = [
                        sys.executable, "-m", "yt_dlp",
                        "-f", fmt,
                        "-o", out,
                        "--no-playlist",
                        "--newline",
                        "--cache-dir", cache_dir,  # Cache-Verzeichnis explizit setzen
                        "--embed-thumbnail",  # Thumbnail in Datei einbetten
                        "--embed-metadata",   # Metadata (Titel, Artist, etc.) einbetten
                    ]
                    if self.ffmpeg_available:
                        # Merge/Remux ins gewünschte Containerformat
                        cmd += ["--merge-output-format", self.download_format.get(), "--format-sort", "res,fps,br"]
                    else:
                        # Ohne ffmpeg: Erzwinge gewünschtes Format durch Remux (falls möglich)
                        # oder akzeptiere was verfügbar ist
                        if self.download_format.get() == "mkv":
                            cmd += ["--remux-video", "mkv"]
                    # Untertitel bewusst NICHT schreiben

                    cmd.append(url)

                    self.progress_queue.put(("progress", progress, f"Lade Video {idx+1} von {total} (Versuch {attempt}/{max_retries})"))
                    
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
                    
                    # Read output line by line to track progress
                    error_output = []
                    for line in (process.stdout or []):
                        line = line.strip()
                        if line:
                            error_output.append(line)
                        if "[download]" in line and "%" in line:
                            # Parse progress from yt-dlp output
                            try:
                                parts = line.split()
                                for part in parts:
                                    if "%" in part:
                                        percent_str = part.replace("%", "")
                                        percent = float(percent_str)
                                        self.progress_queue.put(("current_progress", percent, f"Versuch {attempt}/{max_retries}: {percent:.1f}%"))
                                        break
                            except:
                                pass
                    
                    process.wait(timeout=1800)
                    
                    if process.returncode == 0:
                        success = True
                        self.progress_queue.put(("current_progress", 100, f"Video {idx+1} erfolgreich heruntergeladen"))
                        self.progress_queue.put(("progress", progress, f"Video {idx+1} von {total} fertig"))
                        self.logger("info", f"Video {url} erfolgreich heruntergeladen")
                        
                        break
                    else:
                        if attempt < max_retries:
                            last_errors = "\n".join(error_output[-5:]) if error_output else "Keine Details"
                            self.progress_queue.put(("current_progress", 0, f"Versuch {attempt} fehlgeschlagen: {last_errors[:200]}"))
                            # Schreibe nur die letzten 5 Zeilen ins Log, filtere yt-dlp ERROR/WARNING Präfixe
                            filtered_errors = [line.replace("ERROR: ", "").replace("WARNING: ", "") for line in error_output[-5:]]
                            self.logger("warning", f"Versuch {attempt} für Video {idx+1} fehlgeschlagen:")
                            for err_line in filtered_errors:
                                self.logger("warning", err_line)
                            
                            time.sleep(2)  # Kurze Pause vor erneutem Versuch
                        else:
                            err = "\n".join(error_output[-10:]) if error_output else "Unbekannter Fehler"
                            # Filtere yt-dlp ERROR/WARNING Präfixe
                            filtered_err = err.replace("ERROR: ", "").replace("WARNING: ", "")
                            self.progress_queue.put(("error", f"Fehler bei Video {idx+1} nach {max_retries} Versuchen:\n{filtered_err[:800]}"))
                            self.logger("error", f"Video {idx+1} nach {max_retries} Versuchen fehlgeschlagen:")
                            for err_line in filtered_err.splitlines():
                                self.logger("error", err_line)
                            # Füge zur CSV hinzu
                            self.add_failed_download_to_csv(url, "Video", filtered_err[:500])
                            
                except subprocess.TimeoutExpired:
                    if attempt < max_retries:
                        self.progress_queue.put(("current_progress", 0, f"Timeout bei Versuch {attempt}, versuche erneut..."))
                        self.logger("warning", f"Timeout bei Versuch {attempt} für Video {idx+1}")
                    else:
                        self.progress_queue.put(("error", f"Timeout bei Video {idx+1} nach {max_retries} Versuchen"))
                        self.logger("error", f"Timeout bei Video {idx+1} nach {max_retries} Versuchen")
                        # Füge zur CSV hinzu
                        self.add_failed_download_to_csv(url, "Video", "Timeout nach 10 Versuchen")
                except Exception as e:
                    if attempt < max_retries:
                        self.progress_queue.put(("current_progress", 0, f"Fehler bei Versuch {attempt}, versuche erneut..."))
                        self.logger("warning", f"Fehler bei Versuch {attempt} für Video {idx+1}: {e}")
                    else:
                        self.progress_queue.put(("error", f"Fehler bei Video {idx+1} nach {max_retries} Versuchen: {e}"))
                        self.logger("error", f"Fehler bei Video {idx+1} nach {max_retries} Versuchen: {e}")
                        # Füge zur CSV hinzu
                        self.add_failed_download_to_csv(url, "Video", str(e))

        self.progress_queue.put(("complete", 100, "Alle Downloads abgeschlossen!"))
        self.logger("info", "Alle Downloads abgeschlossen")

    # ---------------------- Audio Download Methods ----------------------
    def browse_audio_folder(self):
        folder = filedialog.askdirectory(initialdir=self.audio_path.get())
        if folder:
            self.audio_path.set(folder)
            self.logger("info", f"Audio-Speicherort geändert: {folder}")

    def on_audio_url_entry_focus_in(self, _):
        if self.audio_url_entry.get() == self.audio_url_placeholder:
            self.audio_url_entry.delete(0, tk.END)
            self.audio_url_entry.config(foreground="black")

    def on_audio_url_entry_focus_out(self, _):
        if not self.audio_url_entry.get().strip():
            self.audio_url_entry.insert(0, self.audio_url_placeholder)
            self.audio_url_entry.config(foreground="grey")

    def add_audio_url_to_list(self):
        url = self.audio_url_entry.get().strip()
        if not url or url == self.audio_url_placeholder:
            messagebox.showwarning("Warnung", "Bitte geben Sie eine URL ein.")
            return
        if not (url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://m.youtube.com/")):
            messagebox.showwarning("Warnung", "Bitte geben Sie eine gültige YouTube-URL ein.")
            return
        
        # Entferne Timeskip-Parameter (&t=... oder ?t=...)
        url = re.sub(r'[&?]t=\d+[smh]?', '', url)
        
        if url in self.audio_links:
            messagebox.showinfo("Info", "Diese URL ist bereits in der Liste.")
            self.logger("info", f"Versuch, doppelte URL hinzuzufügen: {url}")
            return
        
        self.audio_links.append(url)
        self.audio_url_listbox.insert(tk.END, url)
        self.audio_url_entry.delete(0, tk.END)
        self.on_audio_url_entry_focus_out(None)
        self.logger("info", f"Audio-URL zur Liste hinzugefügt: {url}")

    def remove_selected_audio_url(self):
        sel = self.audio_url_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Bitte wählen Sie eine URL aus der Liste aus.")
            return
        idx = sel[0]
        removed_url = self.audio_links[idx]
        self.audio_url_listbox.delete(idx)
        del self.audio_links[idx]
        self.logger("info", f"Audio-URL aus Liste entfernt: {removed_url}")

    def clear_audio_url_list(self):
        if not self.audio_links:
            return
        if messagebox.askyesno("Liste leeren", "Möchten Sie alle URLs aus der Liste entfernen?"):
            count = len(self.audio_links)
            self.audio_links.clear()
            self.audio_url_listbox.delete(0, tk.END)
            self.logger("info", f"Audio-Liste geleert ({count} URLs entfernt)")

    def start_audio_download(self):
        if self.is_downloading_audio:
            messagebox.showinfo("Info", "Download läuft bereits.")
            return
        if not self.audio_links:
            messagebox.showwarning("Warnung", "Bitte fügen Sie mindestens eine URL hinzu.")
            return
        if not os.path.isdir(self.audio_path.get()):
            messagebox.showerror("Fehler", "Der gewählte Speicherort existiert nicht.")
            self.logger("error", "Der gewählte Audio-Speicherort existiert nicht.")
            return

        self.is_downloading_audio = True
        self.audio_download_button.config(text="Download läuft...", state="disabled")
        self.audio_progress_var.set(0)
        self.logger("info", f"Audio-Download gestartet: {len(self.audio_links)} URLs, Format: {self.audio_format.get()}, Ziel: {self.audio_path.get()}")
        threading.Thread(target=self.download_audio, daemon=True).start()

    def download_audio(self):
        # Cache-Ordner für yt-dlp im TEMP-Verzeichnis erstellen (für Thumbnails)
        # Nutze direkt TEMP statt verstecktes .cache Verzeichnis (Windows-kompatibel)
        cache_dir = os.path.join(tempfile.gettempdir(), "yt-dlp-cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        format_type = self.audio_format.get()
        total = len(self.audio_links)
        max_retries = 10
        
        # Starte Downloads
        for idx, url in enumerate(self.audio_links):
            progress = (idx / total) * 100 if total else 0
            self.progress_queue.put(("audio_progress", progress, f"Starte Download {idx+1} von {total}..."))
            self.progress_queue.put(("audio_current_progress", 0, ""))
            
            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    self.progress_queue.put(("audio_current_progress", 0, f"Versuch {attempt}/{max_retries} für Audio {idx+1}"))

                    out = os.path.join(self.audio_path.get(), "%(title)s.%(ext)s")
                    
                    # Zähle vorhandene Dateien vor dem Download
                    output_dir = self.audio_path.get()
                    files_before = set(os.listdir(output_dir)) if os.path.isdir(output_dir) else set()
                    
                    # Download beste Audiospur und konvertiere ins gewählte Format
                    cmd = [
                        sys.executable, "-m", "yt_dlp",
                        "-f", "bestaudio/best",
                        "-x",  # Extract audio
                        "--audio-format", format_type,
                        "--audio-quality", "0",  # beste Qualität
                        "-o", out,
                        "--no-playlist",
                        "--newline",
                        "--cache-dir", cache_dir,  # Cache-Verzeichnis explizit setzen
                        "--add-metadata",  # Fügt alle verfügbaren Metadaten hinzu
                        url
                    ]

                    # Für WAV: Thumbnails/Metadata können nicht sinnvoll eingebettet werden.
                    # Daher nur bei anderen Formaten (z.B. mp3) Thumbnail/Metadata einbetten.
                    if format_type.lower() != "wav":
                        cmd += [
                            "--embed-thumbnail",
                            "--parse-metadata", "%(channel,uploader)s:%(meta_artist)s",  # Channel-Name (nicht Handle) als Artist
                            "--parse-metadata", "%(title)s:%(meta_title)s",  # Titel
                            "--parse-metadata", "%(upload_date>%Y)s:%(meta_date)s",  # Jahr
                            "--replace-in-metadata", "artist", r"^@", ""  # Entferne führendes @ falls vorhanden
                        ]

                    self.progress_queue.put(("audio_progress", progress, f"Lade Audio {idx+1} von {total} (Versuch {attempt}/{max_retries})"))
                    
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

                    # Read output line by line to track progress
                    error_output = []
                    last_status = ""
                    last_destination = None
                    for line in (process.stdout or []):
                        line = line.strip()
                        if line:
                            error_output.append(line)

                        # Capture destination (yt-dlp prints 'Destination: <path>')
                        if 'Destination:' in line:
                            # try to extract the path after 'Destination:'
                            m = re.search(r'Destination:\s*(.+)$', line)
                            if m:
                                last_destination = m.group(1).strip().strip('"')

                        # Zeige verschiedene Phasen des Downloads an
                        if "[download]" in line:
                            if "%" in line:
                                # Parse progress from yt-dlp output
                                try:
                                    parts = line.split()
                                    for part in parts:
                                        if "%" in part:
                                            percent_str = part.replace("%", "")
                                            percent = float(percent_str)
                                            self.progress_queue.put(("audio_current_progress", percent, f"Download: {percent:.1f}%"))
                                            break
                                except:
                                    pass
                            elif "has already been downloaded" in line:
                                last_status = "Bereits heruntergeladen"
                                self.progress_queue.put(("audio_current_progress", 100, last_status))
                        elif "[ExtractAudio]" in line:
                            last_status = "Extrahiere Audio..."
                            self.progress_queue.put(("audio_current_progress", 95, last_status))
                        elif "[EmbedThumbnail]" in line:
                            last_status = "Bette Thumbnail ein..."
                            self.progress_queue.put(("audio_current_progress", 98, last_status))
                        elif "[EmbedMetadata]" in line or "[Metadata]" in line:
                            last_status = "Bette Metadaten ein..."
                            self.progress_queue.put(("audio_current_progress", 99, last_status))
                        elif "Deleting original file" in line:
                            last_status = "Räume auf..."
                            self.progress_queue.put(("audio_current_progress", 99, last_status))

                    process.wait(timeout=1800)

                    # Prüfe ob neue Datei erstellt wurde (Alternative Erfolgsprüfung)
                    files_after = set(os.listdir(output_dir)) if os.path.isdir(output_dir) else set()
                    new_files = files_after - files_before
                    new_audio_files = [f for f in new_files if f.lower().endswith(('.mp3', '.wav', '.m4a', '.opus', '.ogg', '.flac'))]

                    # Wenn Destination erkannt wurde, prüfe das Dateisystem darauf
                    dest_ok = False
                    if last_destination:
                        dest = last_destination
                        # expand and normalize
                        try:
                            dest = os.path.expanduser(dest)
                        except Exception:
                            pass
                        if not os.path.isabs(dest):
                            dest = os.path.join(output_dir, dest)
                        # If file exists directly
                        if os.path.exists(dest) and os.path.splitext(dest)[1].lower() in ('.mp3', '.wav', '.m4a', '.opus', '.ogg', '.flac'):
                            dest_ok = True
                        else:
                            # Try replacing extension with common audio extensions
                            base = os.path.splitext(dest)[0]
                            for ext in ('.mp3', '.wav', '.m4a', '.opus', '.ogg', '.flac'):
                                if os.path.exists(base + ext):
                                    dest_ok = True
                                    break

                    # Erfolg wenn returncode 0 ODER wenn neue Audio-Datei erstellt wurde ODER Destination zeigt auf Audio
                    if process.returncode == 0 or new_audio_files or dest_ok:
                        success = True
                        self.progress_queue.put(("audio_current_progress", 100, f"Audio {idx+1} erfolgreich heruntergeladen"))
                        self.progress_queue.put(("audio_progress", progress, f"Audio {idx+1} von {total} fertig"))
                        # Entferne bei WAV evtl. übrig gebliebene Thumbnail-Dateien (png, webp, jpg)
                        try:
                            if format_type.lower() == "wav":
                                thumb_exts = ('.png', '.jpg', '.jpeg', '.webp')
                                for f in new_files:
                                    if f.lower().endswith(thumb_exts):
                                        p = os.path.join(output_dir, f)
                                        try:
                                            os.remove(p)
                                        except Exception:
                                            pass
                        except Exception:
                            pass

                        self.logger("info", f"Audio {url} erfolgreich heruntergeladen")
                        break
                    else:
                        if attempt < max_retries:
                            last_errors = "\n".join(error_output[-5:]) if error_output else "Keine Details"
                            self.progress_queue.put(("audio_current_progress", 0, f"Versuch {attempt} fehlgeschlagen (Code: {process.returncode}): {last_errors[:200]}"))
                            # Schreibe nur die letzten 5 Zeilen ins Log, filtere yt-dlp ERROR/WARNING Präfixe
                            filtered_errors = [line.replace("ERROR: ", "").replace("WARNING: ", "") for line in error_output[-5:]]
                            self.logger("warning", f"Versuch {attempt} für Audio {idx+1} fehlgeschlagen:")
                            for err_line in filtered_errors:
                                self.logger("warning", err_line)
                            time.sleep(2)  # Kurze Pause vor erneutem Versuch
                        else:
                            err = "\n".join(error_output[-10:]) if error_output else "Unbekannter Fehler"
                            # Filtere yt-dlp ERROR/WARNING Präfixe
                            filtered_err = err.replace("ERROR: ", "").replace("WARNING: ", "")
                            self.progress_queue.put(("audio_error", f"Fehler bei Audio {idx+1} nach {max_retries} Versuchen (Code: {process.returncode}):\n{filtered_err[:800]}"))
                            self.logger("error", f"Audio {idx+1} nach {max_retries} Versuchen fehlgeschlagen:")
                            for err_line in filtered_err.splitlines():
                                self.logger("error", err_line)
                            # Füge zur CSV hinzu
                            self.add_failed_download_to_csv(url, "Audio", filtered_err[:500])
                            
                except subprocess.TimeoutExpired:
                    if attempt < max_retries:
                        self.progress_queue.put(("audio_current_progress", 0, f"Timeout bei Versuch {attempt}, versuche erneut..."))
                        self.logger("warning", f"Timeout bei Versuch {attempt} für Audio {idx+1}")
                    else:
                        self.progress_queue.put(("audio_error", f"Timeout bei Audio {idx+1} nach {max_retries} Versuchen"))
                        self.logger("error", f"Timeout bei Audio {idx+1} nach {max_retries} Versuchen")
                        # Füge zur CSV hinzu
                        self.add_failed_download_to_csv(url, "Audio", "Timeout nach 10 Versuchen")
                except Exception as e:
                    if attempt < max_retries:
                        self.progress_queue.put(("audio_current_progress", 0, f"Fehler bei Versuch {attempt}, versuche erneut..."))
                        self.logger("warning", f"Fehler bei Versuch {attempt} für Audio {idx+1}: {e}")
                    else:
                        self.progress_queue.put(("audio_error", f"Fehler bei Audio {idx+1} nach {max_retries} Versuchen: {e}"))
                        self.logger("error", f"Fehler bei Audio {idx+1} nach {max_retries} Versuchen: {e}")
                        # Füge zur CSV hinzu
                        self.add_failed_download_to_csv(url, "Audio", str(e))

        self.progress_queue.put(("audio_complete", 100, f"Alle {format_type.upper()}-Downloads abgeschlossen!"))
        self.logger("info", "Alle Audio-Downloads abgeschlossen")

    # ---------------------- Extras ----------------------
    def check_formats(self):
        sel = self.url_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Bitte wählen Sie eine URL aus der Liste.")
            return
        url = self.url_links[sel[0]]
        self.status_label.config(text="Prüfe verfügbare Formate...")
        self.logger("info", f"Formatprüfung gestartet für: {url}")

        def worker():
            try:
                r = subprocess.run([sys.executable, "-m", "yt_dlp", "--list-formats", url], capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    win = tk.Toplevel(self.root)
                    win.title("Verfügbare Formate")
                    win.geometry("900x600")
                    txt = tk.Text(win, wrap=tk.NONE)
                    txt.pack(fill=tk.BOTH, expand=True)
                    txt.insert("1.0", r.stdout)
                    txt.config(state=tk.DISABLED)
                    self.progress_queue.put(("format_check_complete", True, ""))
                    self.logger("info", "Formatprüfung erfolgreich abgeschlossen")
                else:
                    self.progress_queue.put(("format_check_complete", False, r.stderr))
                    self.logger("error", f"Formatprüfung fehlgeschlagen: {r.stderr}")
            except Exception as e:
                self.progress_queue.put(("format_check_complete", False, str(e)))
        threading.Thread(target=worker, daemon=True).start()

    # ---------------------- Queue Pump ----------------------
    def check_progress_queue(self):
        try:
            while True:
                msg_type, *data = self.progress_queue.get_nowait()
                if msg_type == "progress":
                    prog, text = data
                    self.progress_var.set(prog)
                    self.status_label.config(text=text)
                elif msg_type == "complete":
                    prog, text = data
                    self.progress_var.set(prog)
                    self.status_label.config(text=text)
                    self.download_button.config(text="Download starten", state="normal")
                    self.is_downloading = False
                    messagebox.showinfo("Erfolg", "Alle Downloads wurden abgeschlossen.")
                elif msg_type == "error":
                    err = data[0]
                    self.status_label.config(text="Fehler beim Download")
                    messagebox.showerror("Download Fehler", err)
                elif msg_type == "install_complete":
                    ok, err = data
                    self.progress_bar.stop(); self.progress_bar.config(mode='determinate')
                    if ok:
                        self.status_label.config(text="yt-dlp installiert/aktualisiert")
                    else:
                        self.status_label.config(text="yt-dlp Installation fehlgeschlagen")
                        messagebox.showerror("Fehler", f"yt-dlp Installation fehlgeschlagen:\n{err}")
                elif msg_type == "format_check_complete":
                    ok, err = data
                    if ok:
                        self.status_label.config(text="Formatprüfung abgeschlossen")
                    else:
                        self.status_label.config(text="Formatprüfung fehlgeschlagen")
                        messagebox.showerror("Fehler", f"Formate konnten nicht abgerufen werden:\n{err}")
                elif msg_type == "audio_progress":
                    prog, text = data
                    self.audio_progress_var.set(prog)
                    self.audio_status_label.config(text=text)
                elif msg_type == "audio_complete":
                    prog, text = data
                    self.audio_progress_var.set(prog)
                    self.audio_status_label.config(text=text)
                    self.audio_download_button.config(text="Download starten", state="normal")
                    self.is_downloading_audio = False
                    messagebox.showinfo("Erfolg", "Alle Audio-Downloads wurden abgeschlossen.")
                elif msg_type == "audio_error":
                    err = data[0]
                    self.audio_status_label.config(text="Fehler beim Download")
                    messagebox.showerror("Download Fehler", err)
                elif msg_type == "current_progress":
                    prog, text = data
                    self.current_progress_var.set(prog)
                    self.current_status_label.config(text=text)
                elif msg_type == "audio_current_progress":
                    prog, text = data
                    self.audio_current_progress_var.set(prog)
                    self.audio_current_status_label.config(text=text)
        except queue.Empty:
            pass
        self.root.after(100, self.check_progress_queue)


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='youtube.ico')
    except Exception:
        pass
    app = YouTubeDownloaderApp(root)

    def on_close():
        if app.is_downloading or app.is_downloading_audio:
            if messagebox.askokcancel("Beenden", "Download läuft noch. Wirklich beenden?"):
                app.logger("info", "Anwendung während laufendem Download beendet")
                root.destroy()
        else:
            app.logger("info", "Anwendung beendet")
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
