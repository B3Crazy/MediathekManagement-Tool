# AniWorldTool

Source-specific CLI tool for downloading, watching, and sync-playing anime episodes from AniWorld.

## 1. Scope

This tool is responsible only for AniWorld-related workflows.

Current implementation:
- `AniLoad.py` command-line entry point
- interactive wizard mode
- direct URL mode (episode, season, series)
- search mode with optional non-interactive selection

## 2. Folder Layout

```text
AniWorldTool/
├── AniLoad.py
└── README.md
```

## 3. Features

- Supports actions: `download`, `watch`, `syncplay`
- Search by anime name (`--search`)
- Interactive episode/season picker
- Batch URL input via CLI and file
- Optional all-language download and merge (`--all-languages`)
- Optional plain output mode (`--no-visual`)
- Provider fallback handling for failed sources

## 4. Requirements

Required:
- Python 3.8+
- `aniworld` package
- ffmpeg in `PATH`

Optional:
- `rich` for enhanced terminal UI

## 5. Installation

Dependencies are managed automatically by the startup scripts.
No manual installation needed.

## 6. Quick Start

**Linux/macOS:**

```bash
cd AniWorldTool
./start.sh
```

**Windows:**

```bash
cd AniWorldTool
start.bat
```

The startup script will:
- Create a virtual environment if needed
- Install all dependencies from `requirements.txt`
- Launch the interactive mode

Hint: Use bash for best visual experience

### Running with arguments

You can pass arguments to the startup scripts:

```bash
# Linux/macOS - search and auto-run first hit
./start.sh --search "Attack on Titan" --no-interactive

# Windows
start.bat --search "Attack on Titan" --no-interactive
```

```bash
# Download a direct URL
./start.sh https://aniworld.to/anime/stream/example-slug
```

## 7. CLI Reference

```text
usage: AniLoad.py [-h] [-f URL_FILE] [-a ACTION] [-s SEARCH]
                  [--no-interactive] [--all-languages] [--no-visual]
                  [urls ...]
```

Arguments:
- `urls`: one or more AniWorld episode/season/series URLs
- `-f`, `--url-file`: text file with one URL per line (`#` comments allowed)
- `-a`, `--action`: `download`, `watch`, or `syncplay`
- `-s`, `--search`: search term to resolve to a series URL
- `--no-interactive`: auto-pick first search result
- `--all-languages`: fetch available language tracks and merge into MKV
- `--no-visual`: disable rich-style progress output

## 8. Common Examples

Batch from file:

```bash
# Linux/macOS
./start.sh --url-file urls.txt --action download

# Windows
start.bat --url-file urls.txt --action download
```

Watch mode:

```bash
# Linux/macOS
./start.sh https://aniworld.to/anime/stream/example-episode --action watch

# Windows
start.bat https://aniworld.to/anime/stream/example-episode --action watch
```

Syncplay mode:

```bash
# Linux/macOS
./start.sh https://aniworld.to/anime/stream/example-episode --action syncplay

# Windows
start.bat https://aniworld.to/anime/stream/example-episode --action syncplay
```

## 9. Output and Behavior

- `download`: delegates to underlying aniworld package download behavior
- `watch`: opens playback through configured provider/player integration
- `syncplay`: delegates sync playback handling to aniworld

The script tries to reduce ffmpeg and warning noise during downloads while still showing relevant failures.

## 10. Troubleshooting

`ModuleNotFoundError: aniworld`
- Install package: `pip install aniworld`

No search results found:
- Try an exact anime title
- Retry later if source is temporarily unavailable

ffmpeg errors:
- Ensure ffmpeg is installed and available in `PATH`
- Verify with `ffmpeg -version`

Provider-specific download failures:
- Re-run; provider fallback may recover
- Try `--all-languages` if only one language track fails

## 11. Known Limitations

- Behavior depends on upstream aniworld package and source site changes
- Provider reliability and available languages vary per episode
- No dedicated test suite is included in this folder yet

## 12. Legal Notice

Use only where legally permitted.
You are responsible for compliance with local laws, platform terms, and copyright regulations.
