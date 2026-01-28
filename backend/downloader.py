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

# Import browser cookie manager
from browser_manager import BrowserCookieManager

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

# Create module-level singleton for browser cookie manager
# This ensures browser detection only happens once
_cookie_manager = BrowserCookieManager()

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
            [sys.executable, "-m", "yt_dlp", "--version"],
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
            [sys.executable, "-m", "yt_dlp", "--list-formats", url],
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
            # With ffmpeg: explicitly select video+audio streams and merge
            # Never fallback to audio-only formats
            return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/bestvideo[ext=mp4]+bestaudio"
        else:
            # Without ffmpeg: get best pre-merged format with video codec
            return "best[vcodec!=none][ext=mp4]/best[vcodec!=none]"
    
    def _download_single(self, url: str, idx: int, attempt: int, max_retries: int):
        """Download a single video with adaptive strategy"""
        output_template = "%(title)s.%(ext)s"
        format_str = self._get_format_string()
        
        # Use module-level cookie manager (already initialized with cached browser)
        strategy = _cookie_manager.get_download_args(attempt)
        
        logging.info(f"Attempt {attempt}/{max_retries} - Strategy: {strategy['description']}")
        
        # Build base command
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", format_str,
            "-o", output_template,
            "--no-playlist",
            "--newline",
            "--cache-dir", self.cache_dir,
            "--embed-thumbnail",
            "--convert-thumbnails", "jpg",
            "--embed-metadata",
            "--no-post-overwrites",
        ]
        
        # Add strategy-specific arguments
        cmd.extend(strategy["cookies"])
        cmd.extend(strategy["client"])
        cmd.extend(strategy["ipv4"])
        cmd.extend(strategy["po_token"])
        cmd.extend(strategy["extra"])
        
        # Add ffmpeg options
        if check_ffmpeg():
            cmd += [
                "--merge-output-format", self.format_type,
                "--format-sort", "res,fps,br"
            ]
        else:
            if self.format_type == "mkv":
                cmd += ["--remux-video", "mkv"]
        
        cmd.append(url)
        
        # Debug logging
        logging.debug(f"Command: {' '.join(cmd)}")
        logging.debug(f"Working directory: {self.output_path}")
        logging.debug(f"Output template: {output_template}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=self.output_path
        )
        
        error_output = []
        has_download_error = False
        bot_detected = False
        has_post_processing_error = False
        
        if process.stdout:
            for line in process.stdout:
                line = line.strip()
                if line:
                    error_output.append(line)
                    
                    # Detect bot-protection error
                    if "Sign in to confirm you're not a bot" in line:
                        bot_detected = True
                        logging.warning("⚠ Bot-protection detected!")
                    
                    # Track actual download errors vs post-processing errors
                    if "ERROR:" in line:
                        if "Postprocessing" in line or "EmbedThumbnail" in line or "thumbnail" in line.lower():
                            has_post_processing_error = True
                        else:
                            has_download_error = True
                
                # Parse progress from yt-dlp output
                if "[download]" in line and "%" in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                percent_str = part.replace("%", "")
                                percent = float(percent_str)
                                self.status.current_file_progress = percent
                                self.status.current_file_message = f"Download: {percent:.1f}% ({strategy['description']})"
                                break
                    except:
                        pass
        
        process.wait(timeout=1800)
        
        # Check if a video file was actually created
        output_dir = self.output_path
        if os.path.isdir(output_dir):
            video_files = [f for f in os.listdir(output_dir) 
                          if f.lower().endswith(('.mp4', '.mkv', '.webm', '.avi'))]
            if video_files:
                if has_post_processing_error:
                    logging.warning(f"✓ Video downloaded (post-processing errors ignored)")
                else:
                    logging.info(f"✓ Video downloaded successfully with strategy: {strategy['description']}")
                return
        
        # Build error message
        if bot_detected:
            err = cookie_mgr.get_user_message()
        elif has_download_error:
            err = "\n".join(error_output[-10:]) if error_output else "Unknown error"
        else:
            err = "Download completed but no video file found"
        
        # Log detailed error
        logging.error(f"✗ Download failed (attempt {attempt}/{max_retries}): {err[:200]}")
        
        raise Exception(f"Download failed: {err}")


class AudioDownloader(BaseDownloader):
    """Download audio from YouTube"""
    
    def _download_single(self, url: str, idx: int, attempt: int, max_retries: int):
        """Download a single audio file with adaptive strategy"""
        output_template = "%(title)s.%(ext)s"
        output_dir = self.output_path
        
        # Get files before download
        files_before = set(os.listdir(output_dir)) if os.path.isdir(output_dir) else set()
        
        # Use module-level cookie manager (already initialized with cached browser)
        strategy = _cookie_manager.get_download_args(attempt)
        
        logging.info(f"Attempt {attempt}/{max_retries} - Strategy: {strategy['description']}")
        
        # Build base command
        cmd = [
            sys.executable, "-m", "yt_dlp",
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
        
        # Add strategy-specific arguments
        cmd.extend(strategy["cookies"])
        cmd.extend(strategy["client"])
        cmd.extend(strategy["ipv4"])
        cmd.extend(strategy["po_token"])
        cmd.extend(strategy["extra"])
        
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
        
        # Debug logging
        logging.debug(f"Command: {' '.join(cmd)}")
        logging.debug(f"Working directory: {self.output_path}")
        logging.debug(f"Output template: {output_template}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=self.output_path
        )
        
        error_output = []
        last_destination = None
        has_post_processing_error = False
        bot_detected = False
        
        if process.stdout:
            for line in process.stdout:
                line = line.strip()
                if line:
                    error_output.append(line)
                    
                    # Detect bot-protection error
                    if "Sign in to confirm you're not a bot" in line:
                        bot_detected = True
                        logging.warning("⚠ Bot-protection detected!")
                    
                    # Track post-processing errors separately
                    if "ERROR:" in line and ("Postprocessing" in line or "thumbnail" in line.lower()):
                        has_post_processing_error = True
                
                # Parse progress from yt-dlp output
                if "[download]" in line and "%" in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                percent_str = part.replace("%", "")
                                percent = float(percent_str)
                                self.status.current_file_progress = percent
                                self.status.current_file_message = f"Download: {percent:.1f}% ({strategy['description']})"
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
        
        # Success if new audio file created OR destination exists (ignore post-processing errors)
        if new_audio_files or dest_ok:
            if has_post_processing_error:
                logging.warning(f"✓ Audio downloaded (post-processing errors ignored)")
            else:
                logging.info(f"✓ Audio downloaded successfully with strategy: {strategy['description']}")
            return
        
        # Build error message
        if bot_detected:
            err = cookie_mgr.get_user_message()
        else:
            err = "\n".join(error_output[-10:]) if error_output else "Unknown error"
        
        # Log detailed error
        logging.error(f"✗ Download failed (attempt {attempt}/{max_retries}): {err[:200]}")
        
        raise Exception(f"Download failed: {err}")

