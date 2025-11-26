#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download logic for MediathekManagement-Tool
Handles video and audio downloads from YouTube
"""

import os
import sys
import subprocess
import tempfile
import time
import csv
import re
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

# Configure logging
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(project_dir, "backend", "logging", "downloader.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True
)

@dataclass
class DownloadStatus:
    """Track download progress and status"""
    task_id: str
    total_files: int
    current_file: int = 0
    progress: float = 0.0
    current_file_progress: float = 0.0
    status: str = "pending"  # pending, downloading, complete, error
    message: str = ""
    current_file_message: str = ""
    failed_urls: List[str] = field(default_factory=list)

def check_ytdlp() -> bool:
    """Check if yt-dlp is available"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_ffmpeg() -> bool:
    """Check if ffmpeg is available"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_available_formats(url: str) -> str:
    """Check available formats for a URL"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--list-formats", url],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(result.stderr)
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while checking formats")
    except Exception as e:
        raise Exception(f"Error checking formats: {str(e)}")

def clean_url(url: str) -> str:
    """Remove timeskip parameters from YouTube URL"""
    return re.sub(r'[&?]t=\d+[smh]?', '', url)

class FailedDownloadLogger:
    """Log failed downloads to CSV"""
    
    def __init__(self):
        self.csv_file = os.path.join(
            project_dir, "backend", "logging", "failed_downloads.csv"
        )
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Type', 'Timestamp', 'Error'])
            logging.info("Created failed downloads CSV file")
    
    def add_session_separator(self):
        """Add a session separator to the CSV"""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['---', '---', '---', '---'])
            logging.info("Added session separator to CSV")
        except Exception as e:
            logging.error(f"Error adding session separator: {e}")
    
    def log_failed_download(self, url: str, download_type: str, error: str = ""):
        """Log a failed download"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([url, download_type, timestamp, error[:500]])
            logging.info(f"Logged failed {download_type} download: {url}")
        except Exception as e:
            logging.error(f"Error writing to CSV: {e}")

class BaseDownloader:
    """Base class for video and audio downloaders"""
    
    def __init__(self, urls: List[str], format_type: str, output_path: str, status: DownloadStatus):
        self.urls = [clean_url(url) for url in urls]
        self.format_type = format_type
        self.output_path = output_path
        self.status = status
        self.failed_logger = FailedDownloadLogger()
        self.cache_dir = os.path.join(tempfile.gettempdir(), "yt-dlp-cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def download_all(self):
        """Download all URLs with retry logic"""
        self.failed_logger.add_session_separator()
        self.status.status = "downloading"
        max_retries = 10
        
        for idx, url in enumerate(self.urls):
            self.status.current_file = idx + 1
            self.status.progress = (idx / len(self.urls)) * 100
            self.status.message = f"Downloading {idx + 1} of {len(self.urls)}..."
            self.status.current_file_progress = 0.0
            self.status.current_file_message = ""
            
            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    logging.info(f"Attempt {attempt}/{max_retries} for {url}")
                    self._download_single(url, idx, attempt, max_retries)
                    success = True
                    break
                except Exception as e:
                    if attempt < max_retries:
                        logging.warning(f"Attempt {attempt} failed: {str(e)}")
                        time.sleep(2)
                    else:
                        logging.error(f"All attempts failed for {url}: {str(e)}")
                        self.status.failed_urls.append(url)
                        self.failed_logger.log_failed_download(
                            url, 
                            self.__class__.__name__, 
                            str(e)
                        )
            
            if success:
                self.status.progress = ((idx + 1) / len(self.urls)) * 100
        
        self.status.status = "complete"
        self.status.progress = 100
        self.status.message = f"Completed! Failed: {len(self.status.failed_urls)}"
        logging.info(f"Download batch complete. Failed: {len(self.status.failed_urls)}")
    
    def _download_single(self, url: str, idx: int, attempt: int, max_retries: int):
        """Override in subclass"""
        raise NotImplementedError

class VideoDownloader(BaseDownloader):
    """Download videos from YouTube"""
    
    def _get_format_string(self) -> str:
        """Get format string based on whether ffmpeg is available"""
        if check_ffmpeg():
            # With ffmpeg: can merge separate streams for 4K/8K
            return (
                "bv*[height>=4320][ext=mp4]+ba[ext=m4a]/"
                "bv*[height>=2160][ext=mp4]+ba[ext=m4a]/"
                "bv*[height>=1080][ext=mp4]+ba[ext=m4a]/"
                "bv*+ba/b"
            )
        else:
            # Without ffmpeg: progressive downloads only
            if self.format_type == "mp4":
                return "b[ext=mp4][height>=720]/b[ext=mp4]/b"
            else:
                return "b[height>=720]/b"
    
    def _download_single(self, url: str, idx: int, attempt: int, max_retries: int):
        """Download a single video"""
        output_template = os.path.join(self.output_path, "%(title)s.%(ext)s")
        format_str = self._get_format_string()
        
        cmd = [
            "yt-dlp",
            "-f", format_str,
            "-o", output_template,
            "--no-playlist",
            "--newline",
            "--cache-dir", self.cache_dir,
            "--embed-thumbnail",
            "--embed-metadata",
        ]
        
        if check_ffmpeg():
            cmd += [
                "--merge-output-format", self.format_type,
                "--format-sort", "res,fps,br"
            ]
        else:
            if self.format_type == "mkv":
                cmd += ["--remux-video", "mkv"]
        
        cmd.append(url)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        error_output = []
        for line in process.stdout:
            line = line.strip()
            if line:
                error_output.append(line)
            
            # Parse progress from yt-dlp output
            if "[download]" in line and "%" in line:
                try:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            percent_str = part.replace("%", "")
                            percent = float(percent_str)
                            self.status.current_file_progress = percent
                            self.status.current_file_message = f"Download: {percent:.1f}%"
                            break
                except:
                    pass
        
        process.wait(timeout=1800)
        
        if process.returncode != 0:
            err = "\n".join(error_output[-10:]) if error_output else "Unknown error"
            raise Exception(f"Download failed: {err}")

class AudioDownloader(BaseDownloader):
    """Download audio from YouTube"""
    
    def _download_single(self, url: str, idx: int, attempt: int, max_retries: int):
        """Download a single audio file"""
        output_template = os.path.join(self.output_path, "%(title)s.%(ext)s")
        output_dir = self.output_path
        
        # Get files before download
        files_before = set(os.listdir(output_dir)) if os.path.isdir(output_dir) else set()
        
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "-x",
            "--audio-format", self.format_type,
            "--audio-quality", "0",
            "-o", output_template,
            "--no-playlist",
            "--newline",
            "--cache-dir", self.cache_dir,
            "--add-metadata",
        ]
        
        # Add metadata/thumbnail for non-WAV formats
        if self.format_type.lower() != "wav":
            cmd += [
                "--embed-thumbnail",
                "--parse-metadata", "%(channel,uploader)s:%(meta_artist)s",
                "--parse-metadata", "%(title)s:%(meta_title)s",
                "--parse-metadata", "%(upload_date>%Y)s:%(meta_date)s",
                "--replace-in-metadata", "artist", r"^@", "",
            ]
        
        cmd.append(url)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        error_output = []
        last_destination = None
        
        for line in process.stdout:
            line = line.strip()
            if line:
                error_output.append(line)
            
            # Parse progress from yt-dlp output
            if "[download]" in line and "%" in line:
                try:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            percent_str = part.replace("%", "")
                            percent = float(percent_str)
                            self.status.current_file_progress = percent
                            self.status.current_file_message = f"Download: {percent:.1f}%"
                            break
                except:
                    pass
            
            # Capture destination
            if 'Destination:' in line:
                m = re.search(r'Destination:\s*(.+)$', line)
                if m:
                    last_destination = m.group(1).strip().strip('"')
        
        process.wait(timeout=1800)
        
        # Check if download was successful
        files_after = set(os.listdir(output_dir)) if os.path.isdir(output_dir) else set()
        new_files = files_after - files_before
        new_audio_files = [f for f in new_files if f.lower().endswith(
            ('.mp3', '.wav', '.m4a', '.opus', '.ogg', '.flac')
        )]
        
        # Check destination
        dest_ok = False
        if last_destination:
            dest = os.path.expanduser(last_destination)
            if not os.path.isabs(dest):
                dest = os.path.join(output_dir, dest)
            
            if os.path.exists(dest) and os.path.splitext(dest)[1].lower() in (
                '.mp3', '.wav', '.m4a', '.opus', '.ogg', '.flac'
            ):
                dest_ok = True
            else:
                base = os.path.splitext(dest)[0]
                for ext in ('.mp3', '.wav', '.m4a', '.opus', '.ogg', '.flac'):
                    if os.path.exists(base + ext):
                        dest_ok = True
                        break
        
        # Clean up WAV thumbnail files
        if self.format_type.lower() == "wav":
            thumb_exts = ('.png', '.jpg', '.jpeg', '.webp')
            for f in new_files:
                if f.lower().endswith(thumb_exts):
                    try:
                        os.remove(os.path.join(output_dir, f))
                    except Exception:
                        pass
        
        # Success if return code is 0 OR new audio file created OR destination exists
        if process.returncode != 0 and not new_audio_files and not dest_ok:
            err = "\n".join(error_output[-10:]) if error_output else "Unknown error"
            raise Exception(f"Download failed: {err}")
