#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API for MediathekManagement-Tool
Provides REST API for video/audio downloads from YouTube
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import uvicorn
import os
import sys
import subprocess
from pathlib import Path
import uuid

from downloader import VideoDownloader, AudioDownloader, DownloadStatus

app = FastAPI(title="MediathekManagement API", version="1.0.0")

# Enable CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for download tasks (in production, use a database)
download_tasks: Dict[str, DownloadStatus] = {}

# Helper function to create timestamped download folder (for web app only)
def create_timestamped_folder(file_count: int) -> str:
    """Create a timestamped folder in user's Downloads directory"""
    from datetime import datetime
    
    # Get user's Downloads folder
    home = Path.home()
    downloads_path = home / "Downloads"
    if not downloads_path.exists():
        downloads_path.mkdir(parents=True, exist_ok=True)
    
    # Create folder name: YYYYMMDD_HHMMSS_filecount
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{timestamp}_{file_count}"
    
    # Create the subfolder
    output_path = downloads_path / folder_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    return str(output_path)

# Helper function to resolve output paths (for desktop app)
def resolve_output_path(path: str) -> str:
    """Resolve output path, converting relative paths to absolute"""
    # If path is just "Downloads", use user's Downloads folder
    if path == "Downloads" or path == "downloads":
        home = Path.home()
        downloads_path = home / "Downloads"
        if not downloads_path.exists():
            downloads_path.mkdir(parents=True, exist_ok=True)
        return str(downloads_path)
    
    # Expand user home directory (~)
    expanded_path = os.path.expanduser(path)
    
    # Convert to absolute path
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
    
    # Create directory if it doesn't exist
    if not os.path.exists(expanded_path):
        try:
            os.makedirs(expanded_path, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Kann Ordner nicht erstellen: {str(e)}")
    
    return expanded_path

# Request/Response models
class DownloadRequest(BaseModel):
    urls: List[HttpUrl]
    format: str  # mp4, mkv for video; mp3, wav for audio
    output_path: str
    use_timestamped_folder: Optional[bool] = False  # True for web app, False for desktop app

class DownloadResponse(BaseModel):
    task_id: str
    message: str
    output_folder: Optional[str] = None  # Return the actual folder path

class StatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    current_file: int
    total_files: int
    message: str
    current_file_progress: float
    current_file_message: str
    failed_urls: List[str]

class FormatCheckRequest(BaseModel):
    url: HttpUrl

@app.get("/")
async def root():
    return {"message": "MediathekManagement API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/download/video", response_model=DownloadResponse)
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Start a video download task
    """
    task_id = str(uuid.uuid4())
    
    # Validate format
    if request.format not in ["mp4", "mkv"]:
        raise HTTPException(status_code=400, detail="Invalid video format. Use 'mp4' or 'mkv'")
    
    # Convert HttpUrl objects to strings
    urls = [str(url) for url in request.urls]
    
    # Determine output path based on request type
    if request.use_timestamped_folder:
        # Web app: create timestamped folder in Downloads
        try:
            output_path = create_timestamped_folder(len(urls))
            print(f"[VIDEO DOWNLOAD - WEB] Created folder: {output_path}")  # Debug logging
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Download-Ordners: {str(e)}")
    else:
        # Desktop app: use provided path
        try:
            output_path = resolve_output_path(request.output_path)
            print(f"[VIDEO DOWNLOAD - DESKTOP] Resolved path: {output_path}")  # Debug logging
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid output path: {str(e)}")
    
    print(f"[VIDEO DOWNLOAD] URLs: {urls}")  # Debug logging
    print(f"[VIDEO DOWNLOAD] Format: {request.format}")  # Debug logging
    
    # Create download status
    status = DownloadStatus(
        task_id=task_id,
        total_files=len(urls),
        status="queued"
    )
    download_tasks[task_id] = status
    
    # Create downloader and start in background
    downloader = VideoDownloader(urls, request.format, output_path, status)
    background_tasks.add_task(downloader.download_all)
    
    return DownloadResponse(
        task_id=task_id,
        message=f"Video download task started with {len(urls)} URLs",
        output_folder=output_path
    )

@app.post("/api/download/audio", response_model=DownloadResponse)
async def download_audio(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Start an audio download task
    """
    task_id = str(uuid.uuid4())
    
    # Validate format
    if request.format not in ["mp3", "wav"]:
        raise HTTPException(status_code=400, detail="Invalid audio format. Use 'mp3' or 'wav'")
    
    # Convert HttpUrl objects to strings
    urls = [str(url) for url in request.urls]
    
    # Determine output path based on request type
    if request.use_timestamped_folder:
        # Web app: create timestamped folder in Downloads
        try:
            output_path = create_timestamped_folder(len(urls))
            print(f"[AUDIO DOWNLOAD - WEB] Created folder: {output_path}")  # Debug logging
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Download-Ordners: {str(e)}")
    else:
        # Desktop app: use provided path
        try:
            output_path = resolve_output_path(request.output_path)
            print(f"[AUDIO DOWNLOAD - DESKTOP] Resolved path: {output_path}")  # Debug logging
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid output path: {str(e)}")
    
    print(f"[AUDIO DOWNLOAD] URLs: {urls}")  # Debug logging
    print(f"[AUDIO DOWNLOAD] Format: {request.format}")  # Debug logging
    
    # Create download status
    status = DownloadStatus(
        task_id=task_id,
        total_files=len(urls),
        status="queued"
    )
    download_tasks[task_id] = status
    
    # Create downloader and start in background
    downloader = AudioDownloader(urls, request.format, output_path, status)
    background_tasks.add_task(downloader.download_all)
    
    return DownloadResponse(
        task_id=task_id,
        message=f"Audio download task started with {len(urls)} URLs",
        output_folder=output_path
    )

@app.get("/api/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str):
    """
    Get the status of a download task
    """
    if task_id not in download_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = download_tasks[task_id]
    
    return StatusResponse(
        task_id=task_id,
        status=status.status,
        progress=status.progress,
        current_file=status.current_file,
        total_files=status.total_files,
        message=status.message,
        current_file_progress=status.current_file_progress,
        current_file_message=status.current_file_message,
        failed_urls=status.failed_urls
    )

@app.post("/api/formats")
async def check_formats(request: FormatCheckRequest):
    """
    Check available formats for a YouTube URL
    """
    from downloader import check_available_formats
    
    try:
        formats = check_available_formats(str(request.url))
        return {"formats": formats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking formats: {str(e)}")

@app.get("/api/tools/check")
async def check_tools():
    """
    Check if required tools (yt-dlp, ffmpeg) are available
    """
    from downloader import check_ytdlp, check_ffmpeg
    
    return {
        "yt_dlp": check_ytdlp(),
        "ffmpeg": check_ffmpeg()
    }

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

from fastapi.responses import StreamingResponse
import asyncio
import json

# Store active search processes
active_searches: Dict[str, subprocess.Popen] = {}

@app.post("/api/search/youtube")
async def search_youtube(request: SearchRequest):
    """
    Search YouTube for videos - streams results as they arrive
    """
    search_id = str(uuid.uuid4())
    
    async def generate_results():
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "yt_dlp", 
                 "ytsearch" + str(request.max_results) + ":" + request.query,
                 "--get-id", "--get-title", "--get-thumbnail", "--get-duration",
                 "--no-warnings", "--no-playlist"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Store process so it can be cancelled
            active_searches[search_id] = process
            
            buffer = []
            try:
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        buffer.append(line)
                        
                        # Every 4 lines = one complete video
                        if len(buffer) == 4:
                            video = {
                                "title": buffer[0],
                                "video_id": buffer[1],
                                "url": f"https://www.youtube.com/watch?v={buffer[1]}",
                                "thumbnail": buffer[2],
                                "duration": buffer[3]
                            }
                            # Send video immediately
                            yield f"data: {json.dumps(video)}\n\n"
                            buffer = []
                            await asyncio.sleep(0.01)  # Small delay for streaming
                
                process.wait()
                yield "data: {\"done\": true}\n\n"
                
            finally:
                if search_id in active_searches:
                    del active_searches[search_id]
                    
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate_results(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Search-ID": search_id
        }
    )

@app.post("/api/search/cancel/{search_id}")
async def cancel_search(search_id: str):
    """
    Cancel an ongoing search
    """
    if search_id in active_searches:
        process = active_searches[search_id]
        process.terminate()
        del active_searches[search_id]
        return {"status": "cancelled"}
    return {"status": "not_found"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
