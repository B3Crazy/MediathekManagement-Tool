# MediathekManagement-Tool

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

A powerful YouTube video and audio downloader with multiple frontend options, powered by a unified Python backend API.

> **🎯 Modern Architecture**: Client-server architecture with a FastAPI backend and multiple frontend implementations (Desktop & Web).

## 🎯 Architecture

This project follows a **client-server architecture**:
- **Backend**: FastAPI server handling all download logic, validation, and processing
- **Frontends**: Multiple UI implementations (Desktop & Web) that communicate with the backend

```
MediathekManagement-Tool/
├── backend/                 # Python FastAPI backend
│   ├── api.py              # REST API endpoints
│   ├── downloader.py       # Download logic with retry mechanism
│   ├── start_server.py     # Server startup script
│   ├── requirements.txt    # Backend dependencies
│   └── logging/            # Logs and failed downloads tracking
│       ├── downloader.log
│       └── failed_downloads.csv
│
├── frontend/
│   ├── desktop/            # Tkinter desktop application
│   │   ├── mediathek_desktop.py
│   │   ├── requirements.txt
│   │   └── start_desktop.bat
│   │
│   ├── web/                # HTML/CSS/JS web application
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── style.css
│   │   └── start_web.bat
│   │
│   └── app/                # Future mobile implementations
│       └── README.md
│
├── documentation/          # Project documentation
├── requirements.txt        # Combined dependencies
└── start.bat              # Quick start script
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

### Backend API (FastAPI)
- ✅ RESTful API with automatic OpenAPI documentation
- ✅ Video downloads (MP4, MKV)
- ✅ Audio downloads (MP3, WAV with metadata)
- ✅ High-quality downloads (up to 4K/8K with ffmpeg)
- ✅ Intelligent retry logic (up to 10 attempts per URL)
- ✅ Real-time progress tracking for each file
- ✅ Background task processing
- ✅ Failed download logging to CSV
- ✅ Metadata and thumbnail embedding
- ✅ CORS support for web frontends
- ✅ URL cleaning (removes timestamp parameters)
- ✅ Health check endpoints

### Desktop Frontend (Tkinter)
- ✅ Native cross-platform desktop GUI
- ✅ Two dedicated tabs: Video & Audio
- ✅ URL list management (add, remove, clear)
- ✅ Overall and per-file progress tracking
- ✅ Format selection (MP4/MKV for video, MP3/WAV for audio)
- ✅ Custom output path selection
- ✅ Backend connection status indicator
- ✅ Real-time download status updates
- ✅ Failed download notifications

### Web Frontend (HTML/CSS/JS)
- ✅ Modern, responsive design
- ✅ Zero dependencies (vanilla JavaScript)
- ✅ Works in any modern browser
- ✅ Real-time progress updates
- ✅ Backend status indicator (online/offline)
- ✅ Tab-based interface (Video/Audio)
- ✅ Clean, intuitive UI
- ✅ Timestamped download folders
- ✅ Per-file and overall progress bars

### Planned Features
- 🔜 Mobile app (React Native/Flutter)
- 🔜 Playlist support
- 🔜 Subtitle downloads
- 🔜 User authentication
- 🔜 Database integration
- 🔜 Docker containerization

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

# Install all dependencies (backend + desktop frontend)
pip install -r requirements.txt

# Or install components individually
pip install -r backend/requirements.txt
pip install -r frontend/desktop/requirements.txt
```

### Component-Specific Installation

**Backend only:**
```bash
pip install -r backend/requirements.txt
```

**Desktop frontend only:**
```bash
pip install -r frontend/desktop/requirements.txt
```

**Web frontend:**
No installation needed! Just open `frontend/web/index.html` in a browser after starting the backend.

### Start Everything

**Windows - Quick start (Backend + Desktop):**
```bash
start.bat
```

This automatically starts both the backend server and desktop frontend.

## 📡 API Endpoints

The backend provides a comprehensive REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and welcome message |
| `/health` | GET | Health check endpoint |
| `/api/download/video` | POST | Start video download task |
| `/api/download/audio` | POST | Start audio download task |
| `/api/status/{task_id}` | GET | Get download progress and status |
| `/api/formats` | POST | Check available formats for URL |
| `/api/tools/check` | GET | Check yt-dlp & ffmpeg availability |

**Interactive API Documentation:**
- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

### Request Examples

**Start Video Download:**
```json
POST /api/download/video
{
  "urls": ["https://youtube.com/watch?v=..."],
  "format": "mp4",
  "output_path": "Downloads",
  "use_timestamped_folder": false
}
```

**Get Download Status:**
```json
GET /api/status/{task_id}

Response:
{
  "task_id": "abc123",
  "status": "downloading",
  "progress": 45.5,
  "current_file": 2,
  "total_files": 5,
  "message": "Downloading 2 of 5...",
  "current_file_progress": 67.3,
  "current_file_message": "Download: 67.3%",
  "failed_urls": []
}
```

## 📝 Configuration

### Backend Configuration
Edit `backend/start_server.py` or `backend/api.py`:
- **Host**: `0.0.0.0` (accessible from all network interfaces)
- **Port**: `8000`
- **CORS**: Enabled for all origins (configure for production!)
- **Auto-reload**: Enabled in development mode

### Frontend Configuration

**Desktop Frontend:**
- Edit `frontend/desktop/mediathek_desktop.py`
- Line 13: `API_URL = "http://localhost:8000"`
- Change to match your backend URL

**Web Frontend:**
- Edit `frontend/web/app.js`
- Line 2: `const API_URL = 'http://localhost:8000';`
- Change to match your backend URL

### Download Behavior

**Desktop Frontend:**
- Uses user-specified output path
- Default: User's Downloads folder
- Files saved directly to chosen location

**Web Frontend:**
- Automatically creates timestamped folders
- Format: `YYYYMMDD_HHMMSS_filecount`
- Location: User's Downloads folder
- Example: `Downloads/20231215_143022_5/`

### Output File Structure

```
{output_path}/
├── {video_title}.mp4
├── {video_title}.mkv
├── {audio_title}.mp3      # With embedded metadata & thumbnail
└── {audio_title}.wav      # WAV format (no thumbnail)
```

### Logging

```
backend/logging/
├── downloader.log          # Detailed download activity
└── failed_downloads.csv    # Failed downloads with timestamps and errors
```

**CSV Format:**
```
URL, Type, Timestamp, Error
https://..., VideoDownloader, 2023-12-15 14:30:22, Download failed: ...
---,---,---,---             # Session separator
```

## 🐛 Troubleshooting

### Backend Issues

**Backend won't start:**
- Check if port 8000 is in use: `netstat -ano | findstr :8000` (Windows)
- Verify Python 3.8+: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`
- Check logs: `backend/logging/downloader.log`

**Port already in use:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <process_id> /F
```

### Frontend Issues

**Desktop frontend can't connect:**
- Ensure backend is running: http://localhost:8000/health
- Check `API_URL` in `mediathek_desktop.py` (line 13)
- Verify firewall settings
- Check CORS configuration in `backend/api.py`

**Web frontend CORS errors:**
- Backend must be running first
- Check browser console for errors
- Verify `allow_origins` in `backend/api.py`
- Clear browser cache and reload

**Web frontend blank page:**
- Check if backend is running
- Open browser console (F12) for errors
- Verify file paths are correct
- Try different browser

### Download Issues

**Downloads fail repeatedly:**
- Verify yt-dlp is installed: `yt-dlp --version`
- Update yt-dlp: `pip install -U yt-dlp`
- Install ffmpeg for better format support
- Check `backend/logging/failed_downloads.csv` for details
- Review `backend/logging/downloader.log`

**No high-quality video options:**
- Install ffmpeg (see System Requirements)
- Without ffmpeg: limited to ~720p progressive downloads
- With ffmpeg: full 4K/8K support

**Audio downloads have no metadata:**
- Ensure ffmpeg is installed
- WAV format doesn't support metadata/thumbnails
- Use MP3 format for metadata and thumbnails

**Slow downloads:**
- Check your internet connection
- YouTube may be rate-limiting
- Try downloading one file at a time
- Consider using VPN if region-blocked

### Permission Issues

**Can't write to output folder:**
```bash
# Check folder permissions
# Create folder manually if it doesn't exist
mkdir "C:\Users\YourName\Downloads\MediathekDownloads"
```

**Python package installation fails:**
```bash
# Try with administrator/sudo
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 🔧 Development

### Project Structure Details

**Backend (`backend/`):**
- `api.py`: FastAPI application with all endpoints
- `downloader.py`: Core download logic with retry mechanism
- `start_server.py`: Server initialization script
- `logging/`: Directory for logs and failed download tracking

**Desktop Frontend (`frontend/desktop/`):**
- `mediathek_desktop.py`: Main Tkinter application
- Uses `requests` library to communicate with backend
- Polls backend for status updates every 500ms

**Web Frontend (`frontend/web/`):**
- Pure HTML/CSS/JavaScript (no build step required)
- `index.html`: Main page structure
- `app.js`: Application logic and API communication
- `style.css`: Styling and responsive design
- Polls backend for status updates every 1000ms

### Adding a New Frontend

1. Create directory in `frontend/`
2. Implement UI that calls backend API endpoints
3. Use the same API contract as existing frontends:
   ```javascript
   // Example: Start video download
   POST /api/download/video
   {
     "urls": ["..."],
     "format": "mp4",
     "output_path": "Downloads",
     "use_timestamped_folder": true/false
   }
   
   // Poll for status
   GET /api/status/{task_id}
   ```
4. Add README with setup instructions
5. Create start script if needed

### Extending the Backend

**Adding new endpoints:**
1. Add route in `backend/api.py`
2. Implement logic in `downloader.py` or create new module
3. Update API documentation in README
4. Test with existing frontends

**Adding new download features:**
1. Extend `BaseDownloader` class in `downloader.py`
2. Add new format options or parameters
3. Update `DownloadRequest` model in `api.py`
4. Test retry logic and error handling

### Code Style

**Python:**
- Follow PEP 8
- Use type hints where applicable
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

**JavaScript:**
- Use modern ES6+ syntax
- Prefer `const`/`let` over `var`
- Add comments for complex logic
- Keep functions pure when possible

### Testing

**Manual Testing Checklist:**
- [ ] Backend starts without errors
- [ ] Health check endpoint responds
- [ ] Desktop frontend connects to backend
- [ ] Web frontend loads and connects
- [ ] Video download (MP4 and MKV)
- [ ] Audio download (MP3 and WAV)
- [ ] Progress tracking works
- [ ] Failed downloads are logged
- [ ] Multiple simultaneous downloads
- [ ] Retry logic on failures

**API Testing:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test tools check
curl http://localhost:8000/api/tools/check

# Test video download
curl -X POST http://localhost:8000/api/download/video \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://youtube.com/watch?v=..."],"format":"mp4","output_path":"Downloads"}'
```

## 🔮 Future Enhancements

### High Priority
- [ ] **Database Integration**: Persistent task storage and history
- [ ] **Download Queue Management**: Pause, resume, and prioritize downloads
- [ ] **Playlist Support**: Download entire YouTube playlists
- [ ] **Subtitle Downloads**: Download and embed subtitles
- [ ] **Quality Selection**: Manual video quality/resolution selection
- [ ] **Download Scheduling**: Schedule downloads for later

### Medium Priority
- [ ] **User Authentication**: Multi-user support with separate accounts
- [ ] **Download History**: Browse and re-download previous items
- [ ] **Batch Operations**: Bulk URL import from file
- [ ] **Custom Metadata**: Edit metadata before download
- [ ] **Bandwidth Control**: Limit download speed
- [ ] **Notification System**: Desktop/email notifications on completion

### Mobile & Advanced
- [ ] **React Native App**: iOS and Android native app
- [ ] **Flutter App**: Cross-platform mobile solution
- [ ] **Progressive Web App (PWA)**: Installable web app
- [ ] **Browser Extension**: Quick download from YouTube pages
- [ ] **Docker Support**: Containerized deployment
- [ ] **Cloud Deployment**: Deploy to AWS/Azure/GCP
- [ ] **API Rate Limiting**: Prevent abuse
- [ ] **WebSocket Support**: Real-time progress without polling

### Quality of Life
- [ ] **Dark Mode**: Theme switching for all frontends
- [ ] **Keyboard Shortcuts**: Faster navigation
- [ ] **Drag & Drop URLs**: Easier URL input
- [ ] **Thumbnail Preview**: Preview before download
- [ ] **Format Conversion**: Convert between formats
- [ ] **Audio Normalization**: Consistent audio levels
- [ ] **Auto-Update**: Automatic yt-dlp updates

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/MediathekManagement-Tool.git
   cd MediathekManagement-Tool
   ```
3. **Create a feature branch:**
   ```bash
   git checkout -b feature/YourAmazingFeature
   ```
4. **Make your changes**
5. **Test thoroughly** with all frontends
6. **Commit your changes:**
   ```bash
   git commit -am 'Add: YourAmazingFeature'
   ```
7. **Push to your branch:**
   ```bash
   git push origin feature/YourAmazingFeature
   ```
8. **Submit a Pull Request**

### Contribution Guidelines

**Code Quality:**
- Follow PEP 8 style for Python code
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Include type hints in Python code
- Keep functions focused and single-purpose

**Testing:**
- Test all changes with both Desktop and Web frontends
- Verify downloads work for video and audio
- Test error handling and edge cases
- Ensure backward compatibility

**Documentation:**
- Update README if adding features
- Add comments for complex logic
- Update API documentation if modifying endpoints
- Include usage examples

**Commit Messages:**
- Use clear, descriptive commit messages
- Format: `Type: Brief description`
- Types: `Add`, `Fix`, `Update`, `Remove`, `Refactor`
- Example: `Add: Playlist download support`

### Areas We Need Help With

- 🐛 Bug fixes and improvements
- 📱 Mobile app development (React Native/Flutter)
- 🎨 UI/UX enhancements
- 📝 Documentation improvements
- 🌍 Internationalization (i18n)
- 🧪 Unit and integration tests
- 🐳 Docker containerization
- ☁️ Cloud deployment guides

### Reporting Issues

When reporting bugs, please include:
- Operating system and version
- Python version
- Exact error message
- Steps to reproduce
- Screenshots if applicable
- Relevant log files (`backend/logging/downloader.log`)

### Feature Requests

Have an idea? Open an issue with:
- Clear description of the feature
- Use case / why it's needed
- Proposed implementation (optional)
- Any relevant examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for **personal use only**. Please respect copyright laws and YouTube's Terms of Service. Only download content you have permission to download or that is licensed for free use.

**Important:**
- Do not use this tool to download copyrighted content without permission
- Respect content creators' rights
- Follow YouTube's Terms of Service
- Use responsibly and legally

## 🙏 Acknowledgments

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: Powerful YouTube downloader
- **[FastAPI](https://fastapi.tiangolo.com/)**: Modern web framework for building APIs
- **[FFmpeg](https://ffmpeg.org/)**: Multimedia framework for video processing
- **Community Contributors**: Thank you for your contributions!

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/B3Crazy/MediathekManagement-Tool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/B3Crazy/MediathekManagement-Tool/discussions)
- **Email**: Create an issue for support

## 📊 Project Status

**Current Version**: 1.0.0  
**Status**: Active Development  
**Last Updated**: November 2025

### Recent Changes
- ✅ Implemented client-server architecture
- ✅ Added FastAPI backend with comprehensive API
- ✅ Created Tkinter desktop frontend
- ✅ Built vanilla JavaScript web frontend
- ✅ Added retry logic (up to 10 attempts)
- ✅ Implemented real-time progress tracking
- ✅ Added failed download logging
- ✅ Embedded metadata and thumbnails

### Next Milestone
- 🎯 Playlist support
- 🎯 Subtitle downloads
- 🎯 Mobile app development

---

**Developed with ❤️ for the community**

If you find this project helpful, give it a ⭐ on GitHub!

[![GitHub stars](https://img.shields.io/github/stars/B3Crazy/MediathekManagement-Tool?style=social)](https://github.com/B3Crazy/MediathekManagement-Tool/stargazers)