#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API for MediathekManagement-Tool
Provides REST API for video/audio downloads from YouTube
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import uvicorn
import os
import sys
import subprocess
from pathlib import Path
import uuid
import zipfile
import shutil
import time

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

# Store zip file paths and folder paths for cleanup
zip_files: Dict[str, tuple[str, str]] = {}  # task_id -> (zip_path, folder_path)

# Helper function to create timestamped download folder (for web app only)
def create_timestamped_folder(file_count: int) -> str:
    """Create a timestamped folder in backend's temp_download directory"""
    from datetime import datetime
    
    # Get backend directory and create temp_download folder
    backend_dir = Path(__file__).parent
    temp_downloads_path = backend_dir / "temp_downloads"
    if not temp_downloads_path.exists():
        temp_downloads_path.mkdir(parents=True, exist_ok=True)
    
    # Create folder name: YYYYMMDD_HHMMSS_filecount
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{timestamp}_{file_count}"
    
    # Create the subfolder
    output_path = temp_downloads_path / folder_name
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
def create_zip_file(folder_path: str, task_id: str) -> str:
    """Create a zip file from the downloaded folder"""
    try:
        # Create zip file name based on folder name
        folder_name = os.path.basename(folder_path)
        zip_path = os.path.join(os.path.dirname(folder_path), f"{folder_name}.zip")
        
        # Create the zip file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the folder
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to zip with relative path
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
        
        # Store zip and folder paths for later cleanup
        zip_files[task_id] = (zip_path, folder_path)
        
        print(f"[ZIP] Created zip file: {zip_path}")
        return zip_path
    except Exception as e:
        print(f"[ZIP ERROR] Failed to create zip: {str(e)}")
        raise

async def create_zip_when_complete(task_id: str, folder_path: str):
    """Background task to create zip file when download is complete"""
    import asyncio
    try:
        # Wait for download to complete
        max_wait = 300  # 5 minutes max
        waited = 0
        while waited < max_wait:
            if task_id in download_tasks:
                status = download_tasks[task_id]
                if status.status == "complete":
                    print(f"[ZIP] Download complete, creating zip for task {task_id}")
                    # Create the zip file
                    zip_path = create_zip_file(folder_path, task_id)
                    # Update status message
                    status.message = "Download complete - ZIP file ready"
                    break
                elif status.status == "error":
                    print(f"[ZIP] Download failed, skipping zip creation for task {task_id}")
                    break
            await asyncio.sleep(1)
            waited += 1
    except Exception as e:
        print(f"[ZIP ERROR] Error in zip creation task: {str(e)}")

async def delayed_cleanup(task_id: str, zip_path: str, folder_path: str):
    """Background task to cleanup files after download has been sent"""
    import asyncio
    try:
        # Wait 30 seconds to give the user time to download the file
        await asyncio.sleep(30)
        
        print(f"[AUTO-CLEANUP] Starting cleanup for task {task_id}")
        
        # Remove zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"[AUTO-CLEANUP] Removed zip: {zip_path}")
        
        # Remove downloaded folder
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"[AUTO-CLEANUP] Removed folder: {folder_path}")
        
        # Remove from tracking
        if task_id in zip_files:
            del zip_files[task_id]
        if task_id in download_tasks:
            del download_tasks[task_id]
            
        print(f"[AUTO-CLEANUP] Cleanup complete for task {task_id}")
    except Exception as e:
        print(f"[AUTO-CLEANUP ERROR] Error cleaning up task {task_id}: {str(e)}")
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
    zip_ready: bool = False
    download_url: Optional[str] = None

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
    
    # Add zip creation task (only for web app with timestamped folders)
    if request.use_timestamped_folder:
        background_tasks.add_task(create_zip_when_complete, task_id, output_path)
    
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
    
    # Add zip creation task (only for web app with timestamped folders)
    if request.use_timestamped_folder:
        background_tasks.add_task(create_zip_when_complete, task_id, output_path)
    
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
    
    # Check if zip file is ready
    zip_ready = task_id in zip_files and status.status == "complete"
    download_url = f"/api/download/zip/{task_id}" if zip_ready else None
    
    return StatusResponse(
        task_id=task_id,
        status=status.status,
        progress=status.progress,
        current_file=status.current_file,
        total_files=status.total_files,
        message=status.message,
        current_file_progress=status.current_file_progress,
        current_file_message=status.current_file_message,
        failed_urls=status.failed_urls,
        zip_ready=zip_ready,
        download_url=download_url
    )

@app.get("/api/download/zip/{task_id}")
async def download_zip(task_id: str):
    """
    Download the zip file for a completed task
    """
    if task_id not in zip_files:
        raise HTTPException(status_code=404, detail="ZIP file not found or not ready yet")
    
    zip_path, folder_path = zip_files[task_id]
    
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP file not found on disk")
    
    # Get the filename for the download
    filename = os.path.basename(zip_path)
    
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.delete("/api/cleanup/{task_id}")
async def cleanup_task(task_id: str):
    """
    Clean up zip file and downloaded folder for a task
    """
    if task_id not in zip_files:
        raise HTTPException(status_code=404, detail="Task not found")
    
    zip_path, folder_path = zip_files[task_id]
    
    try:
        # Remove zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"[CLEANUP] Removed zip: {zip_path}")
        
        # Remove downloaded folder
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"[CLEANUP] Removed folder: {folder_path}")
        
        # Remove from tracking
        del zip_files[task_id]
        if task_id in download_tasks:
            del download_tasks[task_id]
        
        return {"status": "cleaned", "message": "Files removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

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
            # Use JSON output for reliable parsing
            process = subprocess.Popen(
                [sys.executable, "-m", "yt_dlp", 
                 f"ytsearch{request.max_results}:{request.query}",
                 "--dump-single-json",
                 "--no-warnings",
                 "--flat-playlist",
                 "--skip-download"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process so it can be cancelled
            active_searches[search_id] = process
            
            try:
                stdout, stderr = process.communicate(timeout=60)
                
                if process.returncode != 0:
                    yield f"data: {{\"error\": \"Suche fehlgeschlagen: {stderr}\"}}\n\n"
                    return
                
                # Parse JSON response
                data = json.loads(stdout)
                entries = data.get('entries', [])
                
                # Stream results one by one
                for entry in entries:
                    if not entry:
                        continue
                        
                    video_id = entry.get('id', '')
                    title = entry.get('title', 'Unbekannter Titel')
                    duration = entry.get('duration_string', entry.get('duration', 'N/A'))
                    
                    # Format duration if it's a number
                    if isinstance(duration, (int, float)):
                        mins, secs = divmod(int(duration), 60)
                        hours, mins = divmod(mins, 60)
                        if hours > 0:
                            duration = f"{hours}:{mins:02d}:{secs:02d}"
                        else:
                            duration = f"{mins}:{secs:02d}"
                    
                    # Get best thumbnail
                    thumbnails = entry.get('thumbnails', [])
                    thumbnail = thumbnails[-1]['url'] if thumbnails else ''
                    
                    video = {
                        "title": title,
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail": thumbnail,
                        "duration": str(duration)
                    }
                    
                    # Send video immediately
                    yield f"data: {json.dumps(video)}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for streaming
                
                yield "data: {\"done\": true}\n\n"
                
            except subprocess.TimeoutExpired:
                process.kill()
                yield f"data: {{\"error\": \"Suche timeout\"}}\n\n"
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
