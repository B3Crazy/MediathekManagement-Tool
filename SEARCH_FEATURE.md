# YouTube Search Feature

## Overview
A new "YouTube Suche" (YouTube Search) tab has been added to the YouTube Downloader application.

## Features

### Search Tab
- **Search Input**: Enter keywords to search YouTube
- **Result Limit**: Choose between 5, 10, or 20 search results
- **Search Button**: Click to perform the search or press Enter in the search field

### Search Results
Each result displays:
- **Video Title**: The full title of the video (truncated if too long)
- **Duration**: Video length
- **Video ID**: YouTube video identifier
- **URL**: Clickable link to open the video in a browser

### Adding Results to Download Lists
Each search result has two buttons:
- **→ Video hinzufügen**: Add the video URL to the Video download tab
- **→ Audio hinzufügen**: Add the video URL to the Audio download tab

## How to Use

1. **Open the Application**
   - Navigate to the "YouTube Suche" tab

2. **Enter Search Query**
   - Type your search keywords in the search field
   - Select the number of results you want (5, 10, or 20)

3. **Perform Search**
   - Click "Suchen" or press Enter
   - Wait for results to load

4. **Browse Results**
   - Scroll through the results
   - Click on any URL to open it in your browser

5. **Add to Download Lists**
   - Click "→ Video hinzufügen" to add to the video download list
   - Click "→ Audio hinzufügen" to add to the audio download list
   - Switch to the respective tab to start the download

## Technical Details

### Implementation
- Uses `yt-dlp` search functionality (`ytsearch` prefix)
- Retrieves video title, ID, duration, and thumbnail URL
- Runs search in a background thread to prevent UI freezing
- Results are displayed in a scrollable frame

### Search Command
```bash
yt-dlp "ytsearch{N}:{query}" --get-id --get-title --get-duration --get-thumbnail --skip-download
```

Where:
- `{N}` is the number of results (5, 10, or 20)
- `{query}` is the user's search term

### Duplicate Prevention
- The application checks if a URL already exists in the video or audio list
- Shows an info message if the URL is already present
- Prevents duplicate downloads

## Logging
All search activities are logged:
- Search initiated with query
- Search completed with result count
- URLs added to video/audio lists
- Any search errors

## Error Handling
- Timeout protection (60 seconds)
- Error messages for failed searches
- Graceful handling of no results found
