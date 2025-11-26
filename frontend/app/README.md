# MediathekManagement-Tool Mobile App Frontend

## Overview

This directory is reserved for mobile application implementations that will communicate with the same backend API.

## Planned Implementations

### Option 1: React Native
Cross-platform mobile app for iOS and Android using React Native.

**Setup:**
```bash
cd frontend/app/react-native
npx react-native init MediathekApp
```

### Option 2: Flutter
Cross-platform mobile app using Flutter/Dart.

**Setup:**
```bash
cd frontend/app/flutter
flutter create mediathek_app
```

### Option 3: Progressive Web App (PWA)
Convert the web frontend to a PWA for mobile access.

## Backend API Integration

All mobile implementations should connect to the backend API at:
- **Development:** `http://localhost:8000`
- **Production:** Configure with your server URL

## API Endpoints

The mobile app will use the following endpoints:

- `POST /api/download/video` - Start video download
- `POST /api/download/audio` - Start audio download
- `GET /api/status/{task_id}` - Get download status
- `GET /api/tools/check` - Check if yt-dlp and ffmpeg are available
- `GET /health` - Backend health check

## Features to Implement

1. **URL Management**
   - Add/remove YouTube URLs
   - Validate URLs
   - Display URL list

2. **Download Configuration**
   - Select video format (MP4/MKV)
   - Select audio format (MP3/WAV)
   - Set output path

3. **Progress Tracking**
   - Real-time progress updates
   - Status messages
   - Failed downloads list

4. **Notifications**
   - Download completion
   - Error alerts

## Getting Started

Choose your preferred mobile framework and create the project in this directory:

```
frontend/app/
├── react-native/     # React Native implementation
├── flutter/          # Flutter implementation
└── pwa/             # Progressive Web App
```

Each implementation should maintain the same user experience while leveraging the shared backend API.
