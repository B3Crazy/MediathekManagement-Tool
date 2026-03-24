# youtubeTool

Source-specific downloader stack for YouTube media, with a FastAPI backend and a static web frontend.

## 1. Scope

This tool handles YouTube-focused media workflows only.

Current implementation:
- backend API in `backend/`
- browser frontend in `frontend/`
- Linux and Windows startup scripts in source root

## 2. Folder Layout

```text
youtubeTool/
├── backend/
│   ├── api.py
│   ├── downloader.py
│   ├── start_server.py
│   ├── requirements.txt
│   └── logging/
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── themes.css
│   └── README.md
├── requirements.txt
├── start_linux.sh
├── start_windows.bat
└── README.md
```

## 3. Features

Backend:
- FastAPI endpoints for video and audio downloads
- Background task execution and status polling
- URL format checks and tool checks
- CORS enabled for frontend access

Frontend:
- static HTML/CSS/JS web UI
- communicates with backend API on `http://localhost:8000`
- served locally on port `8080` during development/startup

## 4. Requirements

Required:
- Python 3.8+
- packages from `requirements.txt`

Recommended:
- ffmpeg for best format coverage and muxing behavior

## 5. Installation

Dependencies are managed automatically by the startup scripts.
No manual installation needed.

## 6. Quick Start

**Linux:**

```bash
cd youtubeTool
chmod +x start_linux.sh
./start_linux.sh
```

**Windows:**

```bash
cd youtubeTool
start_windows.bat
```

The startup script will:
- create/use `.venv`
- install all dependencies from `requirements.txt`
- check or install ffmpeg where possible
- start backend on `http://localhost:8000`
- serve frontend on `http://localhost:8080`

Open your browser to `http://localhost:8080` to access the UI.

### Manual start (if not using startup scripts)

Backend only:

```bash
cd youtubeTool/backend
python start_server.py
```

In a second terminal, serve the frontend:

```bash
cd youtubeTool/frontend
python -m http.server 8080
```

Then open `http://localhost:8080`.

## 7. API Overview

Main endpoints:
- `GET /health`
- `POST /api/download/video`
- `POST /api/download/audio`
- `GET /api/status/{task_id}`
- `POST /api/formats`
- `GET /api/tools/check`
- `POST /api/search/youtube`

Interactive docs (while backend is running):
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

Example request:

```json
POST /api/download/video
{
  "urls": ["https://www.youtube.com/watch?v=example"],
  "format": "mp4",
  "output_path": "Downloads",
  "use_timestamped_folder": false
}
```

## 8. Output and Logs

- backend runtime logs are stored under `backend/logging/`
- failed download details are tracked in CSV logs
- download output path behavior:
  - desktop-like requests use `output_path`
  - web requests can use timestamped folders in user Downloads

## 9. Troubleshooting

Backend does not start:
- check dependency install: `pip install -r backend/requirements.txt`
- verify Python version (`python --version`)
- confirm port `8000` is free

Frontend cannot connect:
- verify backend health at `http://localhost:8000/health`
- verify frontend is served from `http://localhost:8080`

Downloads fail:
- update yt-dlp: `pip install -U yt-dlp`
- ensure ffmpeg is installed and in `PATH`
- inspect backend logs in `backend/logging/`

## 10. Known Limitations

- No authentication on API by default (development-oriented setup)
- In-memory task storage only (not persistent across restarts)
- Source/provider behavior can break when YouTube changes internals

## 11. Development Notes

- Keep source-specific changes inside this folder
- Prefer documenting new endpoints and request schema changes in this README
- If frontend API base URL changes, update `frontend/app.js` accordingly

## 12. Legal Notice

Use only where legally permitted.
You are responsible for compliance with local laws, platform terms, and copyright regulations.
