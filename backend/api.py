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

# Helper function to resolve output paths
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
    
    # If it's not an absolute path, treat it as invalid for web frontend
    # (to prevent creating folders in unexpected places)
    if not os.path.isabs(expanded_path):
        # For relative paths that aren't "Downloads", reject them
        raise HTTPException(
            status_code=400, 
            detail=f"Bitte geben Sie einen vollständigen Pfad ein (z.B. C:\\Users\\YourName\\Videos). Relativer Pfad '{path}' ist nicht erlaubt."
        )
    
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

class DownloadResponse(BaseModel):
    task_id: str
    message: str

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
    
    # Resolve and validate output path
    try:
        output_path = resolve_output_path(request.output_path)
        print(f"[VIDEO DOWNLOAD] Resolved path: {output_path}")  # Debug logging
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid output path: {str(e)}")
    
    if not os.path.isdir(output_path):
        raise HTTPException(status_code=400, detail="Output path does not exist")
    
    # Convert HttpUrl objects to strings
    urls = [str(url) for url in request.urls]
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
        message=f"Video download task started with {len(urls)} URLs"
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
    
    # Resolve and validate output path
    try:
        output_path = resolve_output_path(request.output_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid output path: {str(e)}")
    
    if not os.path.isdir(output_path):
        raise HTTPException(status_code=400, detail="Output path does not exist")
    
    # Convert HttpUrl objects to strings
    urls = [str(url) for url in request.urls]
    
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
        message=f"Audio download task started with {len(urls)} URLs"
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

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
