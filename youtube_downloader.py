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
from pathlib import Path
import queue
import subprocess


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
        self.makemkv_cmd = "makemkvcon"
        self.makemkv_available = False
        # Checkbox state for DVD titles
        self.selected_title_ids = set()

        # Queues/state
        self.progress_queue = queue.Queue()

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

        # Tab 1: YouTube
        tab_yt = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_yt, text="YouTube Downloader")

        # Tab 2: DVD zu MKV
        tab_dvd = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_dvd, text="DVD → MKV")

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

        # Start
        self.download_button = ttk.Button(tab_yt, text="Download starten", command=self.start_download)
        self.download_button.grid(row=5, column=0, columnspan=2)

        # Layout stretch
        tab_yt.rowconfigure(3, weight=1)
        tab_yt.columnconfigure(0, weight=1)

        # ----- Tab DVD UI -----
        self.makemkv_available = self.check_makemkv()
        dvd_top = ttk.Frame(tab_dvd)
        dvd_top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        dvd_top.columnconfigure(1, weight=1)

        ttk.Label(dvd_top, text="DVD-Laufwerk:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.dvd_drive_var = tk.StringVar(value="")
        self.dvd_drive_combo = ttk.Combobox(dvd_top, textvariable=self.dvd_drive_var, state="readonly", values=[])
        self.dvd_drive_combo.grid(row=0, column=1, sticky="ew")
        ttk.Button(dvd_top, text="Laufwerke scannen", command=self.scan_dvd_drives).grid(row=0, column=2, padx=(8, 0))

        self.dvd_out_path = tk.StringVar(value=str(Path.home() / "Videos"))
        lf_out = ttk.LabelFrame(tab_dvd, text="Ausgabeordner", padding=8)
        lf_out.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_out.columnconfigure(0, weight=1)
        ttk.Entry(lf_out, textvariable=self.dvd_out_path, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(lf_out, text="Durchsuchen", command=self.browse_dvd_output).grid(row=0, column=1)

        lf_titles = ttk.LabelFrame(tab_dvd, text="Titel (Sektionen)", padding=8)
        lf_titles.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        tab_dvd.rowconfigure(2, weight=1)
        tab_dvd.columnconfigure(0, weight=1)
        # Add a checkbox-like column "sel" for selection
        columns = ("sel", "idx", "name", "length", "size")
        self.titles_tree = ttk.Treeview(lf_titles, columns=columns, show="headings", selectmode="extended")
        for col, txt, w, anchor in (("sel", "Auswahl", 80, "center"), ("idx", "#", 60, "w"), ("name", "Titel", 420, "w"), ("length", "Länge", 100, "w"), ("size", "Größe", 120, "w")):
            self.titles_tree.heading(col, text=txt)
            self.titles_tree.column(col, width=w, anchor=anchor)
        self.titles_tree.grid(row=0, column=0, sticky="nsew")
        lf_titles.rowconfigure(0, weight=1); lf_titles.columnconfigure(0, weight=1)
        sb2 = ttk.Scrollbar(lf_titles, orient="vertical", command=self.titles_tree.yview)
        sb2.grid(row=0, column=1, sticky="ns")
        self.titles_tree.config(yscrollcommand=sb2.set)
        # Click to toggle checkbox state in first column
        self.titles_tree.bind("<Button-1>", self.on_titles_click)

        dvd_btns = ttk.Frame(tab_dvd)
        dvd_btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Button(dvd_btns, text="Titel laden", command=self.load_dvd_titles).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(dvd_btns, text="Ausgewählte rippen", command=self.rip_selected_titles).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(dvd_btns, text="In 1 MKV rippen", command=self.rip_selected_titles_merged).pack(side=tk.LEFT)
        self.dvd_status = ttk.Label(tab_dvd, text="Bereit")
        self.dvd_status.grid(row=4, column=0, sticky="w")

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

    def add_url_to_list(self):
        url = self.url_entry.get().strip()
        if not url or url == self.url_placeholder:
            messagebox.showwarning("Warnung", "Bitte geben Sie eine URL ein.")
            return
        if not (url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://m.youtube.com/")):
            messagebox.showwarning("Warnung", "Bitte geben Sie eine gültige YouTube-URL ein.")
            return
        if url in self.url_links:
            messagebox.showinfo("Info", "Diese URL ist bereits in der Liste.")
            return
        self.url_links.append(url)
        self.url_listbox.insert(tk.END, url)
        self.url_entry.delete(0, tk.END)
        self.on_url_entry_focus_out(None)

    def remove_selected_url(self):
        sel = self.url_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Bitte wählen Sie eine URL aus der Liste aus.")
            return
        idx = sel[0]
        self.url_listbox.delete(idx)
        del self.url_links[idx]

    def clear_url_list(self):
        if not self.url_links:
            return
        if messagebox.askyesno("Liste leeren", "Möchten Sie alle URLs aus der Liste entfernen?"):
            self.url_links.clear()
            self.url_listbox.delete(0, tk.END)

    # ---------------------- Tools ----------------------
    def check_ytdlp(self) -> bool:
        try:
            r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=10)
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

    def check_makemkv(self) -> bool:
        # Helper to validate a given command path
        def _validate(cmd: str) -> bool:
            try:
                r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    return True
                out = (r.stdout or "") + (r.stderr or "")
                if "MakeMKV" in out or "makemkvcon" in out.lower():
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            except Exception:
                pass
            # Fallback: try --help
            try:
                r2 = subprocess.run([cmd, "--help"], capture_output=True, text=True, timeout=30)
                out2 = (r2.stdout or "") + (r2.stderr or "")
                if "MakeMKV" in out2 or "makemkvcon" in out2.lower():
                    return True
            except Exception:
                pass
            return False

        # Try current command
        if self.makemkv_cmd and _validate(self.makemkv_cmd):
            return True

        # Search common Windows install paths
        possible = [
            r"C:\\Program Files (x86)\\MakeMKV\\makemkvcon.exe",
            r"C:\\Program Files\\MakeMKV\\makemkvcon.exe",
        ]
        for p in possible:
            if os.path.isfile(p):
                if _validate(p):
                    self.makemkv_cmd = p
                    return True
        return False

    def ensure_makemkv(self) -> bool:
        if self.check_makemkv():
            self.makemkv_available = True
            return True
        # Let user pick makemkvcon.exe
        messagebox.showwarning("MakeMKV fehlt", "Die MakeMKV-CLI (makemkvcon) wurde nicht gefunden. Bitte wählen Sie die makemkvcon.exe aus.")
        path = filedialog.askopenfilename(
            title="makemkvcon.exe auswählen",
            filetypes=[("MakeMKV CLI", "makemkvcon.exe"), ("Alle Dateien", "*.*")]
        )
        if path and os.path.isfile(path):
            self.makemkv_cmd = path
            self.makemkv_available = self.check_makemkv()
        else:
            self.makemkv_available = False
        if not self.makemkv_available:
            # Offer continuing anyway if executable was chosen
            if path and os.path.isfile(path):
                cont = messagebox.askyesno(
                    "MakeMKV",
                    "MakeMKV-CLI konnte nicht eindeutig validiert werden. Trotzdem fortfahren?"
                )
                if cont:
                    self.makemkv_available = True
                    return True
            messagebox.showerror("MakeMKV", "MakeMKV-CLI konnte nicht validiert werden.")
        return self.makemkv_available

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
            return

        self.is_downloading = True
        self.download_button.config(text="Download läuft...", state="disabled")
        self.progress_var.set(0)
        threading.Thread(target=self.download_videos, daemon=True).start()

    def select_format_string(self) -> str:
        # Mit ffmpeg: getrennte Streams (4K/8K) möglich
        if self.ffmpeg_available:
            if self.download_format.get() == "mp4":
                # Bevorzugt MP4-Komponenten, ansonsten beliebig höchste Qualität
                return (
                    "bv*[height>=4320][ext=mp4]+ba[ext=m4a]/"
                    "bv*[height>=2160][ext=mp4]+ba[ext=m4a]/"
                    "bv*+ba/b"
                )
            else:  # mkv
                return (
                    "bv*[height>=4320]+ba/"
                    "bv*[height>=2160]+ba/"
                    "bv*+ba/b"
                )
        # Ohne ffmpeg: nur progressive, versuche min. 720p
        if self.download_format.get() == "mp4":
            return "b[ext=mp4][height>=720]/b[ext=mp4]/b"
        return "b[height>=720]/b"

    def download_videos(self):
        total = len(self.url_links)
        for idx, url in enumerate(self.url_links):
            try:
                progress = (idx / total) * 100 if total else 0
                self.progress_queue.put(("progress", progress, f"Starte Download {idx+1} von {total}..."))

                fmt = self.select_format_string()
                out = os.path.join(self.download_path.get(), "%(title)s.%(ext)s")
                cmd = [
                    "yt-dlp",
                    "-f", fmt,
                    "-o", out,
                    "--no-playlist",
                    "--no-cache-dir",
                ]
                if self.ffmpeg_available:
                    # Merge/Remux ins gewünschte Containerformat
                    cmd += ["--merge-output-format", self.download_format.get(), "--format-sort", "res,fps,br"]
                # Untertitel bewusst NICHT schreiben

                cmd.append(url)

                self.progress_queue.put(("progress", progress, f"Lade Video {idx+1} von {total}..."))
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
                if result.returncode != 0:
                    err = result.stderr or result.stdout or "Unbekannter Fehler"
                    self.progress_queue.put(("error", f"Fehler bei Video {idx+1}: {err[:800]}"))
                else:
                    self.progress_queue.put(("progress", progress, f"Video {idx+1} von {total} fertig"))
            except subprocess.TimeoutExpired:
                self.progress_queue.put(("error", f"Timeout bei Video {idx+1}"))
            except Exception as e:
                self.progress_queue.put(("error", f"Fehler bei Video {idx+1}: {e}"))

        self.progress_queue.put(("complete", 100, "Alle Downloads abgeschlossen!"))

    # ---------------------- DVD Tools ----------------------
    def browse_dvd_output(self):
        folder = filedialog.askdirectory(initialdir=self.dvd_out_path.get())
        if folder:
            self.dvd_out_path.set(folder)

    def scan_dvd_drives(self):
        # Windows: prüfe D:..Z: auf VIDEO_TS
        drives = []
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive) and os.path.isdir(drive):
                if os.path.isdir(os.path.join(drive, "VIDEO_TS")):
                    drives.append(drive)
        if not drives:
            messagebox.showwarning("Kein DVD-Laufwerk", "Es wurde kein DVD-Laufwerk mit VIDEO_TS gefunden.")
        self.dvd_drive_combo["values"] = drives
        if drives:
            self.dvd_drive_combo.current(0)
        self.dvd_status.config(text=f"Gefundene Laufwerke: {', '.join(drives) if drives else '—'}")

    def load_dvd_titles(self):
        if not self.makemkv_available:
            if not self.ensure_makemkv():
                return
        drive = self.dvd_drive_var.get()
        if not drive:
            # Auto-scan and select if possible
            self.scan_dvd_drives()
            vals = list(self.dvd_drive_combo["values"]) or []
            if len(vals) == 1:
                self.dvd_drive_var.set(vals[0])
                drive = vals[0]
            else:
                messagebox.showwarning("Kein Laufwerk", "Bitte zuerst ein DVD-Laufwerk scannen und auswählen.")
                return

        self.dvd_status.config(text="Lese Titel von DVD...")

        def worker():
            try:
                # Ermittle Disc-Index und nutze disc:<idx> für die Titelinfo
                disc_idx = self._get_disc_index_for_drive(drive)
                titles = []
                combined = ""
                if disc_idx is not None:
                    cmd = [self.makemkv_cmd, "-r", "--cache=1", "--progress=-stdout", "info", f"disc:{disc_idx}"]
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    out = (r.stdout or "")
                    err = (r.stderr or "")
                    combined = (out + "\n" + err).strip()
                    titles = self._parse_makemkv_info(out if out else combined)
                else:
                    # Fallback: zeige DRV-Ausgabe
                    r0 = subprocess.run([self.makemkv_cmd, "-r", "--cache=1", "--progress=-stdout", "info"], capture_output=True, text=True, timeout=600)
                    combined = ((r0.stdout or "") + "\n" + (r0.stderr or "")).strip()
                if titles:
                    self.progress_queue.put(("dvd_titles", titles))
                else:
                    msg = combined[:1200] if combined else "(keine Ausgabe)"
                    self.progress_queue.put(("error", f"MakeMKV info Fehler: {msg}"))
            except Exception as e:
                self.progress_queue.put(("error", f"Titel lesen fehlgeschlagen: {e}"))
        threading.Thread(target=worker, daemon=True).start()

    def _parse_makemkv_info(self, text: str):
        # Parsen von Zeilen wie: TINFO:0,2,0,"Name" / TINFO:0,9,0,"3600.000000" / TINFO:0,10,0,"7340032000"
        import re
        titles = {}
        for line in text.splitlines():
            if line.startswith("TINFO:"):
                # TINFO:<idx>,<field>,0,"value"
                m = re.match(r"TINFO:(\d+),(\d+),\d+,\"(.*)\"", line)
                if not m:
                    continue
                idx, field, val = int(m.group(1)), int(m.group(2)), m.group(3)
                t = titles.setdefault(idx, {"name": None, "length": None, "size": None})
                if field in (2, 27) and not t["name"]:  # title name fields (varies)
                    t["name"] = val
                elif field == 9:  # length seconds
                    try:
                        secs = float(val)
                        h = int(secs // 3600); mmin = int((secs % 3600) // 60); s = int(secs % 60)
                        t["length"] = f"{h:02d}:{mmin:02d}:{s:02d}"
                    except Exception:
                        t["length"] = val
                elif field == 10:  # size bytes
                    try:
                        b = int(float(val))
                        t["size"] = f"{b/1_048_576:.1f} MiB"
                    except Exception:
                        t["size"] = val
        # In Liste umwandeln, nach idx sortieren
        result = []
        for idx in sorted(titles.keys()):
            t = titles[idx]
            name = t["name"] or f"Titel {idx}"
            length = t["length"] or "?"
            size = t["size"] or "?"
            result.append((idx, name, length, size))
        return result

    def _parse_disc_index_from_drv(self, text: str, drive: str):
        """Findet in DRV:-Zeilen den Index für das angegebene Windows-Laufwerk (z. B. D:\\)."""
        import re
        d = drive.strip().upper()
        if d.endswith("\\") or d.endswith("/"):
            d = d[:-1]
        if len(d) >= 2 and d[1] == ':':
            d = d[:2]
        # Beispiel: DRV:0,2,999,1,"<model>","<label>","D:"
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("DRV:"):
                continue
            m = re.match(r"^DRV:(\d+)", line)
            if not m:
                continue
            idx = int(m.group(1))
            quoted = re.findall(r'"([^"]*)"', line)
            if quoted:
                last = quoted[-1].upper()
                if last == d:
                    return idx
        return None

    def _get_disc_index_for_drive(self, drive: str):
        """Fragt MakeMKV nach DRV-Liste und liefert den Disc-Index für das gegebene Laufwerk."""
        try:
            r = subprocess.run([self.makemkv_cmd, "-r", "--cache=1", "--progress=-stdout", "info"], capture_output=True, text=True, timeout=120)
            text = (r.stdout or "") + "\n" + (r.stderr or "")
            idx = self._parse_disc_index_from_drv(text, drive)
            if idx is not None:
                return idx
            # Fallback: mit file:<drive> erneut versuchen
            d = drive if drive.endswith("\\") else drive + "\\"
            r2 = subprocess.run([self.makemkv_cmd, "-r", "--cache=1", "--progress=-stdout", "info", f"file:{d}"], capture_output=True, text=True, timeout=120)
            text2 = (r2.stdout or "") + "\n" + (r2.stderr or "")
            return self._parse_disc_index_from_drv(text2, drive)
        except Exception:
            return None

    def rip_selected_titles(self):
        if not self.makemkv_available:
            if not self.ensure_makemkv():
                return
        drive = self.dvd_drive_var.get()
        if not drive:
            messagebox.showwarning("Kein Laufwerk", "Bitte zuerst ein DVD-Laufwerk auswählen.")
            return
        outdir = self.dvd_out_path.get()
        if not os.path.isdir(outdir):
            messagebox.showerror("Fehler", "Ausgabeordner existiert nicht.")
            return
        idxs = self.get_selected_title_indexes()
        if not idxs:
            messagebox.showinfo("Info", "Bitte wählen Sie mindestens einen Titel aus (Checkbox oder Markierung).")
            return

        self.dvd_status.config(text=f"Rippe {len(idxs)} Titel...")

        def worker():
            try:
                disc_idx = self._get_disc_index_for_drive(drive)
                if disc_idx is None:
                    self.progress_queue.put(("error", "Konnte Disc-Index für das Laufwerk nicht ermitteln."))
                    return
                for tidx in idxs:
                    cmd = [self.makemkv_cmd, "-r", "--cache=4", "--progress=-stdout", "mkv", f"disc:{disc_idx}", str(tidx), outdir]
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
                    if r.returncode != 0:
                        self.progress_queue.put(("error", f"Rippen von Titel {tidx} fehlgeschlagen: {r.stderr[:800]}"))
                        return
                self.progress_queue.put(("dvd_rip_complete", len(idxs)))
            except Exception as e:
                self.progress_queue.put(("error", f"Rippen fehlgeschlagen: {e}"))
        threading.Thread(target=worker, daemon=True).start()

    def rip_selected_titles_merged(self):
        # Rippe mehrere Titel und füge sie zu einer MKV zusammen
        if not self.makemkv_available:
            if not self.ensure_makemkv():
                return
        drive = self.dvd_drive_var.get()
        if not drive:
            messagebox.showwarning("Kein Laufwerk", "Bitte zuerst ein DVD-Laufwerk auswählen.")
            return
        outdir = self.dvd_out_path.get()
        if not os.path.isdir(outdir):
            messagebox.showerror("Fehler", "Ausgabeordner existiert nicht.")
            return
        idxs = self.get_selected_title_indexes()
        if not idxs:
            messagebox.showinfo("Info", "Bitte wählen Sie mindestens zwei Titel aus.")
            return
        if len(idxs) == 1:
            # Fallback: nur ein Titel, normal rippen
            self.rip_selected_titles()
            return

        self.dvd_status.config(text=f"Rippe und merge {len(idxs)} Titel...")

        def has_mkvmerge():
            try:
                r = subprocess.run(["mkvmerge", "-V"], capture_output=True, text=True, timeout=10)
                return r.returncode == 0
            except Exception:
                return False

        def worker():
            import tempfile, time, shutil
            try:
                tmpdir = tempfile.mkdtemp(prefix="mkvmerge_", dir=outdir)
                created_files = []
                disc_idx = self._get_disc_index_for_drive(drive)
                if disc_idx is None:
                    self.progress_queue.put(("error", "Konnte Disc-Index für das Laufwerk nicht ermitteln."))
                    shutil.rmtree(tmpdir, ignore_errors=True)
                    return
                for tidx in idxs:
                    before = set(os.listdir(tmpdir))
                    cmd = [self.makemkv_cmd, "-r", "--cache=4", "--progress=-stdout", "mkv", f"disc:{disc_idx}", str(tidx), tmpdir]
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
                    if r.returncode != 0:
                        self.progress_queue.put(("error", f"Rippen von Titel {tidx} fehlgeschlagen: {r.stderr[:800]}"))
                        shutil.rmtree(tmpdir, ignore_errors=True)
                        return
                    after = set(os.listdir(tmpdir))
                    new = sorted(list(after - before))
                    # Pick MKV files only
                    new_mkvs = [os.path.join(tmpdir, n) for n in new if n.lower().endswith(".mkv")]
                    if not new_mkvs:
                        # as fallback, take the newest mkv in directory
                        cand = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.lower().endswith('.mkv')]
                        cand.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                        if cand:
                            new_mkvs = [cand[0]]
                    if not new_mkvs:
                        self.progress_queue.put(("error", f"Konnte MKV-Datei für Titel {tidx} nicht finden."))
                        shutil.rmtree(tmpdir, ignore_errors=True)
                        return
                    created_files.append(new_mkvs[0])

                # Merge step
                ts = time.strftime("%Y%m%d_%H%M%S")
                out_file = os.path.join(outdir, f"DVD_Merged_{ts}.mkv")
                if has_mkvmerge():
                    # mkvmerge append mode
                    # Syntax: mkvmerge -o out.mkv file1.mkv + file2.mkv + file3.mkv
                    merge_cmd = ["mkvmerge", "-o", out_file, created_files[0]]
                    for f in created_files[1:]:
                        merge_cmd += ["+", f]
                    mr = subprocess.run(merge_cmd, capture_output=True, text=True, timeout=7200)
                    if mr.returncode != 0:
                        self.progress_queue.put(("error", f"mkvmerge fehlgeschlagen: {mr.stderr[:800]}"))
                        shutil.rmtree(tmpdir, ignore_errors=True)
                        return
                elif self.ffmpeg_available:
                    # ffmpeg concat demuxer
                    list_path = os.path.join(tmpdir, "concat.txt")
                    with open(list_path, "w", encoding="utf-8") as f:
                        for p in created_files:
                            # Escaping for Windows paths
                            f.write(f"file '{p.replace("'", "'\\''")}'\n")
                    mr = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", out_file], capture_output=True, text=True, timeout=7200)
                    if mr.returncode != 0:
                        self.progress_queue.put(("error", f"ffmpeg Merge fehlgeschlagen: {mr.stderr[:800]}"))
                        shutil.rmtree(tmpdir, ignore_errors=True)
                        return
                else:
                    self.progress_queue.put(("error", "Weder mkvmerge noch ffmpeg verfügbar, kann nicht mergen."))
                    shutil.rmtree(tmpdir, ignore_errors=True)
                    return

                # Cleanup temp
                shutil.rmtree(tmpdir, ignore_errors=True)
                self.progress_queue.put(("dvd_rip_complete", len(idxs)))
            except Exception as e:
                self.progress_queue.put(("error", f"Merge fehlgeschlagen: {e}"))
        threading.Thread(target=worker, daemon=True).start()

    # ----- Treeview checkbox helpers -----
    def on_titles_click(self, event):
        # Toggle checkbox if first column clicked
        region = self.titles_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.titles_tree.identify_column(event.x)  # '#1' -> first
        if col != "#1":
            return
        row = self.titles_tree.identify_row(event.y)
        if not row:
            return
        values = list(self.titles_tree.item(row, 'values'))
        # values: [sel, idx, name, length, size]
        try:
            idx = int(values[1])
        except Exception:
            return
        if values[0] == "[x]":
            values[0] = "[ ]"
            if idx in self.selected_title_ids:
                self.selected_title_ids.remove(idx)
        else:
            values[0] = "[x]"
            self.selected_title_ids.add(idx)
        self.titles_tree.item(row, values=values)

    def get_selected_title_indexes(self):
        # Prefer checkbox selection; fallback to GUI selection
        if self.selected_title_ids:
            return sorted(self.selected_title_ids)
        idxs = []
        for iid in self.titles_tree.selection():
            values = self.titles_tree.item(iid, 'values')
            # if headings were extended, idx is at position 1 now
            try:
                idxs.append(int(values[1]))
            except Exception:
                continue
        return sorted(idxs)

    # ---------------------- Extras ----------------------
    def check_formats(self):
        sel = self.url_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Bitte wählen Sie eine URL aus der Liste.")
            return
        url = self.url_links[sel[0]]
        self.status_label.config(text="Prüfe verfügbare Formate...")

        def worker():
            try:
                r = subprocess.run(["yt-dlp", "--list-formats", url], capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    win = tk.Toplevel(self.root)
                    win.title("Verfügbare Formate")
                    win.geometry("900x600")
                    txt = tk.Text(win, wrap=tk.NONE)
                    txt.pack(fill=tk.BOTH, expand=True)
                    txt.insert("1.0", r.stdout)
                    txt.config(state=tk.DISABLED)
                    self.progress_queue.put(("format_check_complete", True, ""))
                else:
                    self.progress_queue.put(("format_check_complete", False, r.stderr))
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
                elif msg_type == "dvd_titles":
                    titles = data[0]
                    # Clear and insert
                    for iid in self.titles_tree.get_children():
                        self.titles_tree.delete(iid)
                    self.selected_title_ids.clear()
                    for t in titles:
                        # t: (idx, name, length, size)
                        self.titles_tree.insert('', tk.END, values=("[ ]", t[0], t[1], t[2], t[3]))
                    self.dvd_status.config(text=f"{len(titles)} Titel geladen")
                elif msg_type == "dvd_rip_complete":
                    count = data[0]
                    self.dvd_status.config(text=f"Rippen abgeschlossen ({count} Titel)")
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
        if app.is_downloading:
            if messagebox.askokcancel("Beenden", "Download läuft noch. Wirklich beenden?"):
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
