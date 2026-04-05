# MediathekManagement-Tool

A growing collection of source-specific media automation tools.

This repository is organized as a toolbox: each media source has its own folder, its own implementation details, and its own README.

## Purpose

The goal of this project is to keep media workflows modular and maintainable as the number of supported sources grows.

Instead of one large script handling everything, each source is isolated so you can:

- develop and update source logic independently
- ship fixes for one source without risking regressions in others
- keep dependencies scoped to the tools that need them
- document quirks and usage per source in focused READMEs

## Repository Structure

Current top-level layout:

```text
MediathekManagement-Tool/
├── README.md
├── AniWorldTool/
│   ├── AniLoad.py
│   └── README.md
├── primeVideo/
│   ├── prime.py
│   ├── requirements.txt
│   └── README.md
└── youtubeTool/
	 ├── backend/
	 ├── frontend/
	 ├── requirements.txt
	 └── README.md
```

### What each folder means

- `AniWorldTool/`: AniWorld-specific CLI workflow.
- `primeVideo/`: Prime Video-specific CLI helper.
- `youtubeTool/`: YouTube-specific downloader with backend/frontend components.

As this collection grows, new source tools should be added as additional sibling folders.

## Design Principles

Each source tool should follow these principles:

1. Source isolation  
	Keep source-specific logic inside its own folder only.
2. Local documentation  
	Every source folder must include a dedicated README.
3. Minimal coupling  
	Avoid hard dependencies between source folders.
4. Explicit dependencies  
	Keep requirements close to the tool that uses them.
5. Safe-by-default behavior  
	Validate inputs and fail clearly when source behavior changes.

## Tool Runtime Standard

Every source tool folder at repository root must include the following files:

- `requirements.txt`
- `start.sh`
- `start.bat`

Every tool must run inside a local virtual environment in that tool's root folder.

- Required location: `<tool-root>/.venv`
- Example: `MediathekManagement-Tool/AniWorldTool/.venv`

The startup scripts must automatically create `.venv` when it does not exist and then install dependencies from `requirements.txt`.

Minimum startup behavior expected from both script variants:

1. Detect Python 3.8+.
2. Create `.venv` if missing.
3. Activate or directly use the `.venv` Python executable.
4. Install/update dependencies from `requirements.txt`.
5. Start the source tool.

## Quick Start

This repository does not have a single global entry point yet.
Use the startup scripts inside the source folder you want to run.

### Run AniWorld tool

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

See full usage and options in [AniWorldTool/README.md](AniWorldTool/README.md).

### Run YouTube tool

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

See full usage and options in [youtubeTool/README.md](youtubeTool/README.md).

### Run PrimeVideo tool

**Linux/macOS:**

```bash
cd primeVideo
chmod +x start.sh
./start.sh --action tools
```

**Windows:**

```bash
cd primeVideo
start.bat --action tools
```

See full usage and options in [primeVideo/README.md](primeVideo/README.md).

## Adding a New Source Tool

When adding support for a new source, create a new folder at repository root.

Suggested pattern:

```text
newSourceTool/
├── README.md
├── requirements.txt
├── start.sh
├── start.bat
├── backend/                    # optional
├── frontend/                   # optional
└── scripts/                    # optional helper scripts
```

Recommended checklist:

1. Create source folder and initial implementation.
2. Add a source README with:
	- scope and supported URL types
	- install requirements
	- run commands
	- known limitations
	- troubleshooting notes
3. Add mandatory runtime files: `requirements.txt`, `start.sh`, and `start.bat`.
4. Keep any logs, temp files, and caches ignored via `.gitignore`.
5. Link the new source section in this root README.

## Documentation Conventions

To keep the project readable as it grows:

- Root README explains architecture and navigation.
- Source READMEs explain source-specific setup and usage.
- Keep command examples copy/paste-ready.
- Include a short "known issues" section per source.

## Development Notes

- Python is currently the main implementation language.
- Some source tools may include web or desktop frontends.
- Shared utilities can be added later once reuse patterns are stable.

If a utility is truly cross-source, prefer a dedicated shared folder (for example `common/`) rather than importing code between source folders ad hoc.

## Legal and Ethical Use

This repository is intended for personal, lawful media management and automation.

You are responsible for complying with:

- local laws and regulations
- platform terms of service
- copyright and licensing rules in your jurisdiction

Do not use these tools to distribute copyrighted content without permission.

## Roadmap

Planned direction:

- add more source folders over time
- improve consistency of CLIs and APIs across tools
- unify logging and observability patterns
- add automated tests per source where practical
- improve cross-platform startup scripts

## Contributing

Contributions are welcome.

See `CONTRIBUTING.md` for contribution rules, pull request checklist, and source onboarding checklist.

When submitting changes:

1. Keep changes scoped to one source folder when possible.
2. Update the corresponding source README.
3. Include clear reproduction steps for bug fixes.
4. Prefer small, reviewable pull requests.

## Status

This is an active, evolving toolbox. Expect frequent structural and feature changes as new sources are added.
