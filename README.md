# MediathekManagement-Tool

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

A comprehensive YouTube video and audio downloader with multiple frontend options, all powered by a unified Python backend API.

> **🎯 New Architecture**: This project now features a client-server architecture with a FastAPI backend and multiple frontend implementations (Desktop, Web, Mobile).

## 🎯 Architecture

This project follows a **client-server architecture** where:
- **Backend**: FastAPI server handling all download logic, validation, and processing
- **Frontends**: Multiple UI implementations (Desktop, Web, Mobile) that communicate with the backend

```
MediathekManagement-Tool/
├── backend/                 # Python FastAPI backend
│   ├── api.py              # REST API endpoints
│   ├── downloader.py       # Download logic
│   ├── logging/            # Logs and failed downloads
│   └── start_server.py     # Server startup script
│
├── frontend/
│   ├── desktop/            # Tkinter desktop application
│   ├── web/                # HTML/CSS/JS web application
│   └── app/                # Mobile app (future implementations)
│
└── documentation/          # Project documentation
```

## Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [System Requirements](#️-system-requirements)
- [Installation](#-installation)
- [API Documentation](#-api-endpoints)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies (backend + desktop frontend)
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
# Windows
backend\start_backend.bat

# Or manually
cd backend
python start_server.py
```

Backend will be available at: **http://localhost:8000**

### 3. Start a Frontend

#### Desktop Frontend (Tkinter)
```bash
# Windows
frontend\desktop\start_desktop.bat

# Or manually
cd frontend/desktop
python mediathek_desktop.py
```

#### Web Frontend (Browser)
```bash
# Windows
frontend\web\start_web.bat

# Then open http://localhost:8080 in your browser
```

## 📦 Features

### Backend (API)
- ✅ RESTful API with FastAPI
- ✅ Video downloads (MP4, MKV)
- ✅ Audio downloads (MP3, WAV)
- ✅ High-quality downloads (up to 4K/8K with ffmpeg)
- ✅ Retry logic (up to 10 attempts)
- ✅ Progress tracking
- ✅ Failed download logging (CSV)
- ✅ Metadata embedding
- ✅ Thumbnail embedding
- ✅ Background task processing

### Desktop Frontend (Tkinter)
- ✅ Native desktop GUI
- ✅ Two tabs: Video & Audio
- ✅ URL list management
- ✅ Real-time progress tracking
- ✅ Format selection
- ✅ Custom output path

### Web Frontend (HTML/JS)
- ✅ Modern, responsive design
- ✅ No additional dependencies
- ✅ Works in any browser
- ✅ Real-time progress updates
- ✅ Backend status indicator
- ✅ Clean, intuitive UI

### Mobile Frontend (Planned)
- 🔜 React Native (iOS & Android)
- 🔜 Flutter (Cross-platform)
- 🔜 Progressive Web App (PWA)

## 🛠️ System Requirements

### Required
- **Python 3.8+**
- **yt-dlp** (will be installed automatically)

### Optional (Recommended)
- **ffmpeg** (for high-quality video downloads and format conversion)
  - Without ffmpeg: Limited to progressive downloads (max ~720p for most videos)
  - With ffmpeg: Full 4K/8K support with separate audio/video stream merging

### Installing ffmpeg

**Windows:**
```bash
choco install ffmpeg
```
Or download from https://ffmpeg.org/download.html

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg  # RHEL/CentOS
```

## 📥 Installation

### Quick Install

```bash
# Clone repository
git clone https://github.com/B3Crazy/MediathekManagement-Tool.git
cd MediathekManagement-Tool

# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install -r backend/requirements.txt
pip install -r frontend/desktop/requirements.txt
```

### Start Everything

**Windows - Quick start (Backend + Desktop):**
```bash
start.bat
```

This will start both the backend server and desktop frontend automatically.

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/api/download/video` | POST | Start video download |
| `/api/download/audio` | POST | Start audio download |
| `/api/status/{task_id}` | GET | Get download status |
| `/api/formats` | POST | Check available formats |
| `/api/tools/check` | GET | Check yt-dlp & ffmpeg |

Full API documentation available at **http://localhost:8000/docs** (Swagger UI)

## 📝 Configuration

### Backend Configuration
- **Host**: `0.0.0.0` (all interfaces)
- **Port**: `8000`
- **CORS**: Enabled for all origins (configure in production)

### Frontend Configuration
Both frontends connect to: **http://localhost:8000**

To change the backend URL:
- **Desktop**: Edit `frontend/desktop/mediathek_desktop.py` (line 13: `API_URL`)
- **Web**: Edit `frontend/web/app.js` (line 2: `API_URL`)

### Output Structure

```
{output_path}/
├── {video_title}.mp4
├── {video_title}.mkv
├── {audio_title}.mp3
└── {audio_title}.wav
```

Logs and failed downloads:
```
backend/logging/
├── downloader.log          # All download activity
└── failed_downloads.csv    # Failed downloads with timestamps
```

## 🐛 Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify Python 3.8+ is installed: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`

### Frontend can't connect to backend
- Ensure backend is running on http://localhost:8000
- Check backend status: http://localhost:8000/health
- Verify CORS settings in `backend/api.py`

### Downloads fail
- Check if yt-dlp is installed: `yt-dlp --version`
- Install ffmpeg for better quality support
- Check `backend/logging/failed_downloads.csv` for details
- Review `backend/logging/downloader.log`

### Web frontend CORS issues
- Backend must be running first
- Check browser console for errors
- Verify `allow_origins` in `backend/api.py`

## 🔧 Development

### Adding a New Frontend

1. Create a new directory in `frontend/`
2. Implement UI that calls the backend API endpoints
3. Use the same API contract as existing frontends
4. Document setup in a README.md

### Extending the Backend

1. Add new endpoints in `backend/api.py`
2. Implement logic in `backend/downloader.py` or new modules
3. Update API documentation
4. Test with existing frontends

## 🔮 Future Enhancements

- [ ] Database integration for task persistence
- [ ] User authentication and multi-user support
- [ ] Download queue management
- [ ] Playlist support
- [ ] Subtitle download options
- [ ] Video quality selection
- [ ] Mobile app implementations (React Native, Flutter)
- [ ] Docker containerization
- [ ] Cloud deployment guides

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Make your changes
4. Test with all frontends
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature/YourFeature`
7. Submit a pull request

### Guidelines
- Follow PEP 8 style for Python code
- Add docstrings for new functions
- Test your changes thoroughly
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal use only. Please respect copyright laws and YouTube's Terms of Service. Only download content you have permission to download.

---

**Developed with ❤️ for the community**

If you find this project helpful, give it a ⭐ on GitHub!