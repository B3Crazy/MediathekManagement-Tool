#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Frontend for MediathekManagement-Tool
Tkinter GUI that calls the backend API
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import time
from pathlib import Path
import queue
from PIL import Image, ImageTk
from io import BytesIO
import os
import hashlib

# Backend API URL
API_URL = "http://localhost:8000"

class ThumbnailCache:
    """Caches downloaded YouTube thumbnails locally"""
    def __init__(self):
        self.cache_dir = Path.home() / ".mediathek_cache" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_path(self, url: str) -> Path:
        """Get cache file path for a thumbnail URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.jpg"
    
    def get_thumbnail(self, url: str, max_width: int = 120) -> ImageTk.PhotoImage:
        """
        Get cached or downloaded thumbnail as PhotoImage
        Returns a PIL Image resized to max_width
        """
        cache_path = self.get_cache_path(url)
        
        # Try to load from cache
        if cache_path.exists():
            try:
                img = Image.open(cache_path)
                return self._resize_image(img, max_width)
            except Exception:
                pass
        
        # Download and cache
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                # Save to cache
                img.save(cache_path, "JPEG")
                return self._resize_image(img, max_width)
        except Exception:
            pass
        
        # Return placeholder if download fails
        return self._create_placeholder(max_width)
    
    def _resize_image(self, img: Image.Image, max_width: int) -> ImageTk.PhotoImage:
        """Resize image maintaining aspect ratio"""
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    
    def _create_placeholder(self, size: int) -> ImageTk.PhotoImage:
        """Create a placeholder image"""
        img = Image.new("RGB", (size, int(size * 0.5625)), color="gray")
        return ImageTk.PhotoImage(img)

class MediathekDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MediathekManagement-Tool - Desktop")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # Thumbnail cache
        self.thumbnail_cache = ThumbnailCache()

        # State
        self.download_format = tk.StringVar(value="mp4")
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_links = []
        self.current_task_id = None

        # Audio tab states
        self.audio_format = tk.StringVar(value="mp3")
        self.audio_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.audio_links = []
        self.current_audio_task_id = None

        # Search tab states
        self.search_results = []
        self.search_format = tk.StringVar(value="mp4")  # Selected format for search results
        self.search_type = tk.StringVar(value="video")  # video or audio

        # Status update queue
        self.status_queue = queue.Queue()
        
        # Image references for thumbnails
        self.thumbnail_references = []

        # Build UI
        self.create_widgets()

        # Check backend connection
        self.check_backend()

        # Start status updater
        self.update_status()

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

        # Tab 3: YouTube Search
        tab_search = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab_search, text="YouTube Suche")

        # ----- Tab YouTube UI -----
        self._create_video_tab(tab_yt)
        
        # ----- Tab Audio UI -----
        self._create_audio_tab(tab_audio)

        # ----- Tab Search UI -----
        self._create_search_tab(tab_search)

    def _create_video_tab(self, tab_yt):
        """Create video download tab"""
        # Format selection
        lf_format = ttk.LabelFrame(tab_yt, text="Video Format", padding=8)
        lf_format.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Radiobutton(lf_format, text="MP4", variable=self.download_format, value="mp4").grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(lf_format, text="MKV", variable=self.download_format, value="mkv").grid(row=0, column=1)

        # Output path
        lf_path = ttk.LabelFrame(tab_yt, text="Speicherort", padding=8)
        lf_path.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_path.columnconfigure(0, weight=1)
        self.path_entry = ttk.Entry(lf_path, textvariable=self.download_path, state="readonly")
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(lf_path, text="Durchsuchen", command=self.browse_folder).grid(row=0, column=1)

        # URL entry
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

        # URL list
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
        ttk.Button(btns, text="Liste leeren", command=self.clear_url_list).pack(side=tk.LEFT)

        # Progress
        lf_prog = ttk.LabelFrame(tab_yt, text="Download-Status", padding=8)
        lf_prog.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_prog.columnconfigure(0, weight=1)
        
        # Overall progress
        ttk.Label(lf_prog, text="Gesamtfortschritt:").grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(lf_prog, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        
        self.status_label = ttk.Label(lf_prog, text="Bereit zum Download")
        self.status_label.grid(row=2, column=0, sticky="w", pady=(0, 10))
        
        # Current file progress
        ttk.Label(lf_prog, text="Aktueller Download:").grid(row=3, column=0, sticky="w", pady=(0, 3))
        self.current_file_progress_var = tk.DoubleVar(value=0)
        self.current_file_progress_bar = ttk.Progressbar(lf_prog, variable=self.current_file_progress_var, maximum=100)
        self.current_file_progress_bar.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        
        self.current_file_status_label = ttk.Label(lf_prog, text="")
        self.current_file_status_label.grid(row=5, column=0, sticky="w")

        # Download button
        self.download_button = ttk.Button(tab_yt, text="Download starten", command=self.start_download)
        self.download_button.grid(row=5, column=0, columnspan=2)

        # Layout stretch
        tab_yt.rowconfigure(3, weight=1)
        tab_yt.columnconfigure(0, weight=1)

    def _create_audio_tab(self, tab_audio):
        """Create audio download tab"""
        # Format selection
        lf_audio_format = ttk.LabelFrame(tab_audio, text="Audio Format", padding=8)
        lf_audio_format.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Radiobutton(lf_audio_format, text="MP3", variable=self.audio_format, value="mp3").grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(lf_audio_format, text="WAV", variable=self.audio_format, value="wav").grid(row=0, column=1)

        # Output path
        lf_audio_path = ttk.LabelFrame(tab_audio, text="Speicherort", padding=8)
        lf_audio_path.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_audio_path.columnconfigure(0, weight=1)
        self.audio_path_entry = ttk.Entry(lf_audio_path, textvariable=self.audio_path, state="readonly")
        self.audio_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(lf_audio_path, text="Durchsuchen", command=self.browse_audio_folder).grid(row=0, column=1)

        # URL entry
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

        # URL list
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
        
        # Overall progress
        ttk.Label(lf_audio_prog, text="Gesamtfortschritt:").grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.audio_progress_var = tk.DoubleVar(value=0)
        self.audio_progress_bar = ttk.Progressbar(lf_audio_prog, variable=self.audio_progress_var, maximum=100)
        self.audio_progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        
        self.audio_status_label = ttk.Label(lf_audio_prog, text="Bereit zum Download")
        self.audio_status_label.grid(row=2, column=0, sticky="w", pady=(0, 10))
        
        # Current file progress
        ttk.Label(lf_audio_prog, text="Aktueller Download:").grid(row=3, column=0, sticky="w", pady=(0, 3))
        self.audio_current_file_progress_var = tk.DoubleVar(value=0)
        self.audio_current_file_progress_bar = ttk.Progressbar(lf_audio_prog, variable=self.audio_current_file_progress_var, maximum=100)
        self.audio_current_file_progress_bar.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        
        self.audio_current_file_status_label = ttk.Label(lf_audio_prog, text="")
        self.audio_current_file_status_label.grid(row=5, column=0, sticky="w")

        # Download button
        self.audio_download_button = ttk.Button(tab_audio, text="Download starten", command=self.start_audio_download)
        self.audio_download_button.grid(row=5, column=0, columnspan=2)

        # Layout stretch
        tab_audio.rowconfigure(3, weight=1)
        tab_audio.columnconfigure(0, weight=1)

    def _create_search_tab(self, tab_search):
        """Create YouTube search tab"""
        # Search input
        lf_search = ttk.LabelFrame(tab_search, text="Nach Videos suchen", padding=8)
        lf_search.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        lf_search.columnconfigure(0, weight=1)
        
        self.search_entry = ttk.Entry(lf_search)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        ttk.Button(lf_search, text="Suchen", command=self.perform_search).grid(row=0, column=1)

        # Format selection for search results
        lf_search_format = ttk.LabelFrame(tab_search, text="Format für Search-Ergebnisse", padding=8)
        lf_search_format.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(lf_search_format, text="Video:").grid(row=0, column=0, padx=(0, 8))
        ttk.Radiobutton(lf_search_format, text="MP4", variable=self.search_format, value="mp4").grid(row=0, column=1, padx=(0, 12))
        ttk.Radiobutton(lf_search_format, text="MKV", variable=self.search_format, value="mkv").grid(row=0, column=2, padx=(0, 24))
        
        ttk.Label(lf_search_format, text="Audio:").grid(row=0, column=3, padx=(0, 8))
        ttk.Radiobutton(lf_search_format, text="MP3", variable=self.search_format, value="mp3").grid(row=0, column=4, padx=(0, 12))
        ttk.Radiobutton(lf_search_format, text="WAV", variable=self.search_format, value="wav").grid(row=0, column=5)

        # Search results
        lf_results = ttk.LabelFrame(tab_search, text="Suchergebnisse", padding=8)
        lf_results.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        lf_results.rowconfigure(0, weight=1)
        lf_results.columnconfigure(0, weight=1)

        # Canvas for scrollable results
        self.search_canvas = tk.Canvas(lf_results, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(lf_results, orient="vertical", command=self.search_canvas.yview)
        self.search_results_frame = ttk.Frame(self.search_canvas)
        
        self.search_results_frame.bind(
            "<Configure>",
            lambda e: self.search_canvas.configure(scrollregion=self.search_canvas.bbox("all"))
        )
        
        self.search_canvas.create_window((0, 0), window=self.search_results_frame, anchor="nw")
        self.search_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.search_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Search status label
        self.search_status_label = ttk.Label(tab_search, text="Bereit zur Suche", foreground="blue")
        self.search_status_label.grid(row=3, column=0, columnspan=2, sticky="ew")

        # Layout stretch
        tab_search.rowconfigure(2, weight=1)
        tab_search.columnconfigure(0, weight=1)

    # ----- Backend Communication -----
    
    def check_backend(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="Backend verbunden")
                self.audio_status_label.config(text="Backend verbunden")
            else:
                self.show_backend_error()
        except requests.exceptions.RequestException:
            self.show_backend_error()
    
    def show_backend_error(self):
        """Show error if backend is not available"""
        error_msg = (
            "Backend-Server nicht erreichbar!\n\n"
            "Bitte starten Sie den Backend-Server mit:\n"
            "backend\\start_backend.bat\n\n"
            "Oder führen Sie aus:\n"
            "python backend/start_server.py"
        )
        messagebox.showerror("Backend nicht verfügbar", error_msg)
        self.status_label.config(text="Backend nicht verfügbar")
        self.audio_status_label.config(text="Backend nicht verfügbar")

    # ----- Video Tab Methods -----
    
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
            self.status_label.config(text="⚠ Bitte geben Sie eine URL ein")
            return
        if not (url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://m.youtube.com/")):
            self.status_label.config(text="⚠ Bitte geben Sie eine gültige YouTube-URL ein")
            return
        if url in self.url_links:
            self.status_label.config(text="ℹ Diese URL ist bereits in der Liste")
            return
        
        self.url_links.append(url)
        self.url_listbox.insert(tk.END, url)
        self.url_entry.delete(0, tk.END)
        self.on_url_entry_focus_out(None)
        self.status_label.config(text=f"✓ URL hinzugefügt ({len(self.url_links)} in Liste)")

    def remove_selected_url(self):
        sel = self.url_listbox.curselection()
        if not sel:
            self.status_label.config(text="ℹ Bitte wählen Sie eine URL aus der Liste aus")
            return
        idx = sel[0]
        self.url_listbox.delete(idx)
        del self.url_links[idx]
        self.status_label.config(text=f"✓ URL entfernt ({len(self.url_links)} in Liste)")

    def clear_url_list(self):
        if not self.url_links:
            return
        count = len(self.url_links)
        self.url_links.clear()
        self.url_listbox.delete(0, tk.END)
        self.status_label.config(text=f"✓ Liste geleert ({count} URLs entfernt)")

    def start_download(self):
        """Start video download via backend API"""
        if not self.url_links:
            self.status_label.config(text="⚠ Bitte fügen Sie mindestens eine URL hinzu")
            return
        
        # Prepare request
        data = {
            "urls": self.url_links,
            "format": self.download_format.get(),
            "output_path": self.download_path.get()
        }
        
        # Send to backend
        def send_request():
            try:
                response = requests.post(f"{API_URL}/api/download/video", json=data, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    self.current_task_id = result["task_id"]
                    self.status_queue.put(("video_started", result["message"]))
                else:
                    self.status_queue.put(("error", f"Fehler: {response.text}"))
            except Exception as e:
                self.status_queue.put(("error", f"Verbindungsfehler: {str(e)}"))
        
        self.download_button.config(state="disabled", text="Download läuft...")
        threading.Thread(target=send_request, daemon=True).start()

    # ----- Audio Tab Methods -----
    
    def on_audio_url_entry_focus_in(self, _):
        if self.audio_url_entry.get() == self.audio_url_placeholder:
            self.audio_url_entry.delete(0, tk.END)
            self.audio_url_entry.config(foreground="black")

    def on_audio_url_entry_focus_out(self, _):
        if not self.audio_url_entry.get().strip():
            self.audio_url_entry.insert(0, self.audio_url_placeholder)
            self.audio_url_entry.config(foreground="grey")

    def browse_audio_folder(self):
        folder = filedialog.askdirectory(initialdir=self.audio_path.get())
        if folder:
            self.audio_path.set(folder)

    def add_audio_url_to_list(self):
        url = self.audio_url_entry.get().strip()
        if not url or url == self.audio_url_placeholder:
            self.audio_status_label.config(text="⚠ Bitte geben Sie eine URL ein")
            return
        if not (url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://m.youtube.com/")):
            self.audio_status_label.config(text="⚠ Bitte geben Sie eine gültige YouTube-URL ein")
            return
        if url in self.audio_links:
            self.audio_status_label.config(text="ℹ Diese URL ist bereits in der Liste")
            return
        
        self.audio_links.append(url)
        self.audio_url_listbox.insert(tk.END, url)
        self.audio_url_entry.delete(0, tk.END)
        self.on_audio_url_entry_focus_out(None)
        self.audio_status_label.config(text=f"✓ URL hinzugefügt ({len(self.audio_links)} in Liste)")

    def remove_selected_audio_url(self):
        sel = self.audio_url_listbox.curselection()
        if not sel:
            self.audio_status_label.config(text="ℹ Bitte wählen Sie eine URL aus der Liste aus")
            return
        idx = sel[0]
        self.audio_url_listbox.delete(idx)
        del self.audio_links[idx]
        self.audio_status_label.config(text=f"✓ URL entfernt ({len(self.audio_links)} in Liste)")

    def clear_audio_url_list(self):
        if not self.audio_links:
            return
        count = len(self.audio_links)
        self.audio_links.clear()
        self.audio_url_listbox.delete(0, tk.END)
        self.audio_status_label.config(text=f"✓ Liste geleert ({count} URLs entfernt)")
    # ----- Search Tab Methods -----
    
    def perform_search(self):
        """Search YouTube for videos"""
        query = self.search_entry.get().strip()
        if not query:
            self.search_status_label.config(text="⚠ Bitte geben Sie einen Suchbegriff ein", foreground="red")
            return
        
        self.search_status_label.config(text="🔍 Suche läuft...", foreground="blue")
        
        def search():
            try:
                response = requests.post(
                    f"{API_URL}/api/search/youtube",
                    json={"query": query, "max_results": 10},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.search_results = data["results"]
                    self.status_queue.put(("search_results", len(self.search_results)))
                else:
                    self.status_queue.put(("search_error", f"Server: {response.text[:100]}"))
            except Exception as e:
                self.status_queue.put(("search_error", str(e)))
        
        threading.Thread(target=search, daemon=True).start()
    
    def display_search_results(self):
        """Display search results with thumbnails"""
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        if not self.search_results:
            label = ttk.Label(self.search_results_frame, text="Keine Ergebnisse gefunden")
            label.pack(pady=20)
            return
        
        for video in self.search_results:
            self._create_search_result_card(video)
    
    def _create_search_result_card(self, video: dict):
        """Create a card for a single search result"""
        card = ttk.Frame(self.search_results_frame, relief="solid", borderwidth=1)
        card.pack(fill="x", padx=5, pady=5)
        
        # Left: Thumbnail
        thumbnail_frame = ttk.Frame(card)
        thumbnail_frame.pack(side="left", padx=8, pady=8)
        
        # Get thumbnail image
        img = self.thumbnail_cache.get_thumbnail(video["thumbnail_url"])
        thumb_label = tk.Label(thumbnail_frame, image=img, bg="gray")
        self.thumbnail_references.append(img)  # Keep reference to prevent garbage collection
        thumb_label.pack()
        
        # Middle: Video info
        info_frame = ttk.Frame(card)
        info_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        
        title_label = ttk.Label(info_frame, text=video["title"], font=("", 10, "bold"), wraplength=300, justify="left")
        title_label.pack(anchor="w")
        
        channel_label = ttk.Label(info_frame, text=f"Channel: {video['channel']}", font=("", 9), foreground="gray")
        channel_label.pack(anchor="w", pady=(3, 0))
        
        duration_label = ttk.Label(info_frame, text=f"Duration: {video['duration']}", font=("", 9), foreground="gray")
        duration_label.pack(anchor="w")
        
        # Right: Add to list button
        button_frame = ttk.Frame(card)
        button_frame.pack(side="right", padx=8, pady=8)
        
        format_str = self.search_format.get()
        if format_str in ("mp4", "mkv"):
            type_label = "Video"
        else:
            type_label = "Audio"
        
        btn = ttk.Button(
            button_frame,
            text=f"Zur Liste\n({format_str.upper()})",
            command=lambda url=video["url"]: self.add_search_result_to_list(url)
        )
        btn.pack()
    
    def add_search_result_to_list(self, url: str):
        """Add a search result to the appropriate download list"""
        format_str = self.search_format.get()
        
        if format_str in ("mp4", "mkv"):
            # Video format
            if url in self.url_links:
                self.search_status_label.config(text="ℹ Diese URL ist bereits in der Video-Liste", foreground="blue")
                return
            self.url_links.append(url)
            self.url_listbox.insert(tk.END, url)
            self.search_status_label.config(text=f"✓ URL zur Video-Liste hinzugefügt ({len(self.url_links)} in Liste)", foreground="green")
        else:
            # Audio format
            if url in self.audio_links:
                self.search_status_label.config(text="ℹ Diese URL ist bereits in der Audio-Liste", foreground="blue")
                return
            self.audio_links.append(url)
            self.audio_url_listbox.insert(tk.END, url)
            self.search_status_label.config(text=f"✓ URL zur Audio-Liste hinzugefügt ({len(self.audio_links)} in Liste)", foreground="green")
    def start_audio_download(self):
        """Start audio download via backend API"""
        if not self.audio_links:
            self.audio_status_label.config(text="⚠ Bitte fügen Sie mindestens eine URL hinzu")
            return
        
        # Prepare request
        data = {
            "urls": self.audio_links,
            "format": self.audio_format.get(),
            "output_path": self.audio_path.get()
        }
        
        # Send to backend
        def send_request():
            try:
                response = requests.post(f"{API_URL}/api/download/audio", json=data, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    self.current_audio_task_id = result["task_id"]
                    self.status_queue.put(("audio_started", result["message"]))
                else:
                    self.status_queue.put(("audio_error", f"Fehler: {response.text}"))
            except Exception as e:
                self.status_queue.put(("audio_error", f"Verbindungsfehler: {str(e)}"))
        
        self.audio_download_button.config(state="disabled", text="Download läuft...")
        threading.Thread(target=send_request, daemon=True).start()

    # ----- Status Updates -----
    
    def update_status(self):
        """Poll for status updates"""
        try:
            while True:
                msg_type, *data = self.status_queue.get_nowait()
                
                if msg_type == "video_started":
                    self.status_label.config(text=data[0])
                elif msg_type == "audio_started":
                    self.audio_status_label.config(text=data[0])
                elif msg_type == "error":
                    self.status_label.config(text=f"❌ Fehler: {data[0][:50]}...")
                    self.download_button.config(state="normal", text="Download starten")
                elif msg_type == "audio_error":
                    self.audio_status_label.config(text=f"❌ Fehler: {data[0][:50]}...")
                    self.audio_download_button.config(state="normal", text="Download starten")
                elif msg_type == "search_results":
                    result_count = data[0]
                    self.search_status_label.config(text=f"✓ {result_count} Ergebnisse gefunden", foreground="green")
                    self.display_search_results()
                elif msg_type == "search_error":
                    error_msg = data[0]
                    self.search_status_label.config(text=f"❌ Fehler: {error_msg[:50]}...", foreground="red")
                    
        except queue.Empty:
            pass
        
        # Poll backend for active tasks
        if self.current_task_id:
            self.poll_video_status()
        if self.current_audio_task_id:
            self.poll_audio_status()
        
        self.root.after(500, self.update_status)
    
    def poll_video_status(self):
        """Poll backend for video download status"""
        def check():
            try:
                response = requests.get(f"{API_URL}/api/status/{self.current_task_id}", timeout=5)
                if response.status_code == 200:
                    status = response.json()
                    self.progress_var.set(status["progress"])
                    self.status_label.config(text=status["message"])
                    
                    # Update current file progress
                    current_file_progress = status.get("current_file_progress", 0)
                    self.current_file_progress_var.set(current_file_progress)
                    current_file_msg = status.get("current_file_message", "")
                    if current_file_msg:
                        self.current_file_status_label.config(text=current_file_msg)
                    else:
                        self.current_file_status_label.config(text="")
                    
                    if status["status"] == "complete":
                        self.download_button.config(state="normal", text="Download starten")
                        self.current_task_id = None
                        self.current_file_progress_var.set(0)
                        self.current_file_status_label.config(text="")
                        failed = len(status['failed_urls'])
                        if failed > 0:
                            self.status_label.config(text=f"✓ Download abgeschlossen! ⚠ {failed} fehlgeschlagen")
                        else:
                            self.status_label.config(text="✓ Alle Downloads erfolgreich abgeschlossen!")
            except Exception:
                pass
        
        threading.Thread(target=check, daemon=True).start()
    
    def poll_audio_status(self):
        """Poll backend for audio download status"""
        def check():
            try:
                response = requests.get(f"{API_URL}/api/status/{self.current_audio_task_id}", timeout=5)
                if response.status_code == 200:
                    status = response.json()
                    self.audio_progress_var.set(status["progress"])
                    self.audio_status_label.config(text=status["message"])
                    
                    # Update current file progress
                    current_file_progress = status.get("current_file_progress", 0)
                    self.audio_current_file_progress_var.set(current_file_progress)
                    current_file_msg = status.get("current_file_message", "")
                    if current_file_msg:
                        self.audio_current_file_status_label.config(text=current_file_msg)
                    else:
                        self.audio_current_file_status_label.config(text="")
                    
                    if status["status"] == "complete":
                        self.audio_download_button.config(state="normal", text="Download starten")
                        self.current_audio_task_id = None
                        self.audio_current_file_progress_var.set(0)
                        self.audio_current_file_status_label.config(text="")
                        failed = len(status['failed_urls'])
                        if failed > 0:
                            self.audio_status_label.config(text=f"✓ Download abgeschlossen! ⚠ {failed} fehlgeschlagen")
                        else:
                            self.audio_status_label.config(text="✓ Alle Downloads erfolgreich abgeschlossen!")
            except Exception:
                pass
        
        threading.Thread(target=check, daemon=True).start()


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default='youtube.ico')
    except Exception:
        pass
    app = MediathekDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
