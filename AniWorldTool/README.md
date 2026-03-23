# AniLoad - CLI Tool for AniWorld Anime Downloads

<div align="center">

```
█████████               ███  █████                              █████
  ███░░░░░███             ░░░  ░░███                              ░░███
 ░███    ░███  ████████   ████  ░███         ██████   ██████    ███████
 ░███████████ ░░███░░███ ░░███  ░███        ███░░███ ░░░░░███  ███░░███
 ░███░░░░░███  ░███ ░███  ░███  ░███       ░███ ░███  ███████ ░███ ░███
 ░███    ░███  ░███ ░███  ░███  ░███      █░███ ░███ ███░░███ ░███ ░███
 █████   █████ ████ █████ █████ ███████████░░██████ ░░████████░░████████
░░░░░   ░░░░░ ░░░░ ░░░░░ ░░░░░ ░░░░░░░░░░░  ░░░░░░   ░░░░░░░░  ░░░░░░░░
```

**A powerful, non-interactive command-line interface for downloading and managing anime episodes from AniWorld**

</div>

## Overview

AniLoad is a sophisticated command-line wrapper around the [aniworld](https://github.com/phoenixthrush/AniWorld-Downloader) Python package. It provides both **interactive and automation-friendly interfaces** for downloading, watching, and syncing anime episodes from AniWorld (aniworld.to and s.to).

### Key Features

- 🎬 **Multiple Actions**: Download, watch (with external players), or sync episodes with SyncPlay
- 🔍 **Smart Search**: Interactive and non-interactive search with rich HTML parsing
- 📦 **Batch Operations**: Process multiple URLs or entire series/seasons at once
- 🎭 **Multi-Language Support**: Download multiple dubs/subs and merge into single MKV files
- ⚡ **Parallel Downloads**: Intelligent worker-based parallel downloading with automatic retry
- 🎨 **Visual Progress**: Beautiful progress bars and status tracking (with optional plain-text fallback)
- 🚀 **URL File Support**: Load URLs from text files (one URL per line)
- 🛡️ **Robust Error Handling**: Automatic retry logic for failed downloads with fallback providers
- 🔗 **Multiple URL Types**: Support for series, seasons, and individual episodes

---

## Installation

### Prerequisites

- **Python 3.7+** (3.9+ recommended)
- **FFmpeg** (required for encoding downloaded videos)
- **aniworld package** (automatically handles dependencies)

### Setup Steps

1. **Install the aniworld package:**
   ```bash
   pip install aniworld
   ```

2. **Run AniLoad:**
   ```bash
   python AniLoad.py
   ```

### Optional Dependencies

For enhanced visual output, install the `rich` library:
```bash
pip install rich
```

If `rich` is not available, AniLoad falls back to simple text-based prompts while maintaining full functionality.

---

## Usage

### Interactive Mode (Default)

Simply run the script without arguments to enter the interactive wizard:

```bash
python AniLoad.py
```

The interactive mode guides you through:
1. **Search** for anime by name
2. **Select** the desired series from results
3. **View** series information (title, year, rating, genres, description)
4. **Choose** seasons to download
5. **Pick** specific episodes
6. **Configure** download options (language, MKV merge, visual progress)

### Command-Line Arguments

```
usage: AniLoad.py [-h] [-f URL_FILE] [-a ACTION] [-s SEARCH] 
                   [--no-interactive] [--all-languages] [--no-visual]
                   [urls ...]

positional arguments:
  urls                   Episode, season, or series URLs

options:
  -h, --help            Show help message
  -f FILE, --url-file FILE
                        Text file with one URL per line
  -a ACTION, --action ACTION
                        Action to run: download, watch, or syncplay
                        (default: download)
  -s SEARCH, --search SEARCH
                        Search by series name and auto-pick first result
  --no-interactive      Disable interactive menu (auto-pick first search result)
  --all-languages       Download all available dubs/subs and merge into one MKV
  --no-visual           Disable visual progress console (use plain text)
```

---

## Examples

### 1. Interactive Mode - Full Wizard

```bash
python AniLoad.py
```
Opens the complete interactive interface where you can search, browse, select, and configure everything.

### 2. Download a Specific Episode

```bash
python AniLoad.py https://aniworld.to/anime/stream/episode-slug
```

### 3. Download an Entire Season

```bash
python AniLoad.py https://aniworld.to/anime/stream/season-slug
```

### 4. Download Full Series

```bash
python AniLoad.py https://aniworld.to/anime/stream/series-slug
```

### 5. Search and Download

```bash
python AniLoad.py --search "Attack on Titan"
```
Non-interactive search that auto-selects the first result and opens the interactive episode selector.

### 6. Non-Interactive Search and Download

```bash
python AniLoad.py --search "Demon Slayer" --no-interactive
```
Automatically selects the first search result and first episode (useful for scripting).

### 7. Download with All Language Tracks

```bash
python AniLoad.py https://aniworld.to/anime/stream/episode-slug --all-languages
```
Downloads all available audio tracks (German Dub, English Dub, etc.) and merges them into a single MKV file with multiple audio streams.

### 8. Batch Download from File

Create a file `urls.txt`:
```
https://aniworld.to/anime/stream/episode-1
https://aniworld.to/anime/stream/episode-2
https://aniworld.to/anime/stream/episode-3
```

Then download:
```bash
python AniLoad.py --url-file urls.txt --all-languages
```

### 9. Watch Instead of Download

```bash
python AniLoad.py https://aniworld.to/anime/stream/episode-slug --action watch
```
Streams the episode in your configured video player (requires external player configuration in aniworld).

### 10. SyncPlay Synchronization

```bash
python AniLoad.py https://aniworld.to/anime/stream/episode-slug --action syncplay
```
Syncs video playback across multiple devices using SyncPlay protocol.

### 11. Disable Visual Progress

```bash
python AniLoad.py https://aniworld.to/anime/stream/series-slug --no-visual
```
Uses plain text progress instead of rich visual interface (useful for CI/CD or remote servers).

### 12. Multiple URLs with Different Actions

```bash
python AniLoad.py \
  https://aniworld.to/anime/stream/episode-1 \
  https://aniworld.to/anime/stream/episode-2 \
  --all-languages \
  --action download
```

---

## Features in Detail

### 🔍 Search Functionality

- **Interactive Search**: Full-featured terminal UI with table displays (requires Rich library)
- **Fallback Mode**: Plain text menus when Rich is unavailable
- **HTML Parsing**: Automatic HTML entity decoding and HTML tag removal
- **URL Validation**: Only processes valid AniWorld anime URLs

### 📥 Download Features

#### Multi-Language Support
- Detects all available audio/subtitle tracks for each episode
- Merges multiple language versions into single MKV with multiple audio streams
- Respects language preferences from aniworld package configuration

#### Smart Provider Selection
- Automatically tries preferred providers (Filemoon, Vidmoly, VOE) first
- Falls back to alternative providers if primary fails
- Configurable provider priority in code

#### Parallel Processing
- Intelligently determines optimal number of worker threads (1-10)
- Thread-safe download queue with automatic load balancing
- Separate retry phase for failed downloads
- Lock-based synchronization for progress updates

#### Progress Tracking
- Real-time progress bars with elapsed time display
- Per-worker status showing current episode and language
- Overall progress tracking across all workers
- Clear formatting with episode/season/language information

#### Robust Error Handling
- Progressive fallback: tries multiple providers per language
- Automatic retry phase for failed downloads
- Detailed error reporting with failure summaries
- Graceful handling of network interruptions (via aniworld package)

### 📝 URL File Handling

- Reads one URL per line from text files
- Skips empty lines and comments (lines starting with `#`)
- Combines file URLs with command-line arguments
- Useful for batch operations and automation

### 🎭 Episode Selection

Supports flexible selection syntax:
- **Single**: `5` - select episode 5
- **Range**: `1-5` - select episodes 1 through 5
- **Multiple ranges**: `1,3,5-7,10` - select mixed selection
- **All**: `all` or `a` or `*` - select all episodes

### 🎨 Visual Frontend

**Features (with Rich library):**
- Color-coded tables for series/seasons/episodes
- Structured panels with series information
- Interactive prompts with validation
- Episode metadata display (title, available languages, providers)
- Download progress with multiple simultaneous workers

**Fallback (without Rich):**
- Plain text numbered lists for selections
- Simple yes/no prompts
- Basic progress indication via console output

### 🔧 Output Suppression

- Automatically suppresses FFmpeg output during downloads (less clutter)
- Suppresses aniworld package warning logs during downloads
- Preserves error messages and user prompts
- Maintains full control with `--no-visual` option

---

## Configuration

### aniworld Package Configuration

AniLoad respects all aniworld package environment variables and settings:

```bash
# Use SerienStream (s.to) instead of AniWorld:
export ANIWORLD_USE_STO_SEARCH=1
python AniLoad.py --search "Your Anime"

# Use HTTP for s.to IP address (186.2.175.5):
# Configuration handled automatically by aniworld package
```

### Default Actions

AniLoad recognizes these actions (from aniworld.config.ACTION_METHODS):
- `download` - Downloads episodes to configured download directory
- `watch` - Streams episodes in external player
- `syncplay` - Enables SyncPlay synchronization

### FFmpeg Configuration

FFmpeg is called automatically for encoding multi-language MKV files. Ensure FFmpeg is installed and accessible in your PATH:

```bash
# Verify FFmpeg installation:
ffmpeg -version
```

---

## How It Works

### Program Flow

1. **Initialization**
   - Loads aniworld package components
   - Parses command-line arguments
   - Initializes Rich components (or falls back to basic text)

2. **URL Resolution**
   - User provides URLs directly OR
   - Searches for series name OR
   - Launches interactive episode selector

3. **Episode Listing**
   - Parses provider data to extract available languages and providers
   - Displays metadata (title, ratings, descriptions, available tracks)
   - Allows flexible episode selection

4. **Download Configuration**
   - Determines action (download, watch, syncplay)
   - For downloads: configures multi-language and visual options
   - Prepares job queue for processing

5. **Execution**
   - **Download Action**: Uses multi-threaded worker pool with fallback providers
   - **Watch Action**: Delegates to aniworld's watch functionality
   - **SyncPlay Action**: Delegates to aniworld's syncplay functionality

6. **Progress Tracking** (for downloads)
   - Workers pull jobs from queue
   - Each job processes all selected language tracks
   - Failed jobs go to retry queue with reduced workers
   - Final summary of failures (if any)

### Provider Selection Strategy

For each episode + language combination:

1. **Preferred Providers**: Try Filemoon, Vidmoly, VOE in order
2. **Fallback Providers**: Try other available providers from response
3. **Default**: Fall back to VOE if nothing available
4. **Error Handling**: Retry with different providers automatically

---

## Advantages Over Interactive aniworld Menu

| Feature | AniLoad | aniworld Menu |
|---------|---------|---------------|
| **Command-line driven** | ✅ | ❌ |
| **Batch processing** | ✅ | ❌ |
| **URL file support** | ✅ | ❌ |
| **Parallel downloads** | ✅ | ❌ |
| **Automation scripts** | ✅ | ❌ |
| **Interactive terminal** | ✅ | ✅ |
| **Rich visual UI** | ✅ | ✅ |
| **Multiple actions** | ✅ | ✅ |
| **Multi-language merge** | ✅ | ⚠️ |

---

## Troubleshooting

### Issue: "ModuleNotFoundError: aniworld"

**Solution**: Install the aniworld package
```bash
pip install aniworld
```

### Issue: "No matching stream results found"

**Solutions**:
- Try a different anime name (use exact titiles)
- Check your internet connection
- Verify AniWorld service is accessible: `https://aniworld.to`

### Issue: Download fails with provider errors

**Automatic handling**:
- AniLoad automatically tries alternative providers
- Failed downloads are automatically retried
- Check console output for specific error messages

**Manual fixes**:
- Verify episodes are in German language (AniWorld's primary language)
- Try using `--all-languages` to access all available tracks

### Issue: FFmpeg not found

**Solutions**:
```bash
# Windows: Install via Chocolatey
choco install ffmpeg

# macOS: Install via Homebrew
brew install ffmpeg

# Linux: Install via package manager
sudo apt-get install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg      # CentOS/RHEL
```

### Issue: Rich library not available

**Solution**: Install optional dependency
```bash
pip install rich
```

AniLoad will work without it, but with reduced visual appeal.

### Issue: Very slow downloads

**Possible causes**:
- Network connectivity issues (check your internet speed)
- Provider servers overloaded (try different time)
- Too many concurrent workers causing throttling

**Solutions**:
- Reduce concurrent downloads by modifying `max_workers` (line ~800)
- Try downloading single episodes first to test connection
- Use `--no-visual` to reduce CPU overhead

---

## Advanced Usage

### Integration with Automation Tools

#### Cron Job Example (Linux/macOS)
```bash
# Daily download of latest episodes (requires URL file)
0 2 * * * cd /path/to/AniWorldTool && python AniLoad.py --url-file daily_episodes.txt --no-visual

# Note: Update daily_episodes.txt with current episode URLs
```

#### GitHub Actions Example
```yaml
- name: Download Latest Anime
  run: |
    pip install aniworld rich
    python AniLoad.py --search "Attack on Titan" --no-interactive --no-visual
```

### Modify Download Behavior

Edit `AniLoad.py` to customize:

**Change maximum workers** (line ~800):
```python
max_workers = max(1, min(len(jobs), 5))  # Reduce from 10 to 5
```

**Change preferred providers** (line 24):
```python
PREFERRED_PROVIDERS = ("Vidmoly", "Filemoon", "VOE")
```

**Suppress FFmpeg output** (automatically done, but can be disabled)

---

## Architecture

### Key Functions

| Function | Purpose |
|----------|---------|
| `_interactive_frontend_wizard()` | Full interactive episode selection UI |
| `_search_url_from_name()` | Non-interactive search and auto-selection |
| `_download_with_visual_frontend()` | Parallel download with rich progress |
| `_build_visual_jobs()` | Prepare download job queue |
| `_worker()` | Thread worker for parallel downloads |
| `_build_object()` | Resolve URL to Series/Season/Episode object |

### Data Flow

```
User Input
    ↓
URL Resolution (Direct / Search / Interactive)
    ↓
Object Building (Series → Seasons → Episodes)
    ↓
Job Queue Creation
    ↓
Worker Thread Pool
    ↓
Provider Selection & Download
    ↓
Retry Phase (if failures)
    ↓
Final Summary
```

---

## License

This tool wraps the [aniworld](https://github.com/phoenixthrush/AniWorld-Downloader) package. Please respect the original package's license terms.

For anime content, ensure you have proper rights and comply with local laws and platform terms of service.

---

## Contributing & Support

**Issues or improvements?**
- Check the code comments for implementation details
- Review the aniworld package documentation: https://github.com/phoenixthrush/AniWorld-Downloader
- Modify functions directly as needed for your use case

---

## Changelog

### v1.0.0
- Initial release
- Full interactive and non-interactive modes
- Multi-language support with MKV merging
- Parallel download processing
- Comprehensive error handling and retry logic
- Rich visual frontend with fallback text mode

---

## Quick Reference

```bash
# Interactive mode
python AniLoad.py

# Download specific URL(s)
python AniLoad.py <URL1> <URL2> ...

# Search and download
python AniLoad.py --search "anime name"
python AniLoad.py --search "anime name" --no-interactive

# Batch from file
python AniLoad.py --url-file urls.txt

# Multi-language MKV
python AniLoad.py <URL> --all-languages

# Watch instead of download
python AniLoad.py <URL> --action watch

# Minimal output (CI/CD)
python AniLoad.py <URL> --no-visual

# Combine options
python AniLoad.py --search "anime" --all-languages --no-visual
```

---

**Enjoy your anime downloads! 🎉**
