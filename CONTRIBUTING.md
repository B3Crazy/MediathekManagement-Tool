# Contributing

This repository is a growing collection of source-specific media tools.

Please keep contributions modular, documented, and easy to review.

## Contribution Rules

- Keep changes scoped to one source folder when possible.
- Avoid introducing cross-source coupling unless explicitly required.
- Update README files for any behavior, setup, or command changes.
- Keep scripts and commands cross-platform where practical.
- Do not commit secrets, local paths, or generated cache files.
- Every source tool must include `requirements.txt`, `start.sh`, and `start.bat`.
- Every source tool must run inside `<tool-root>/.venv`.
- Startup scripts must auto-create `.venv` when missing and install dependencies from `requirements.txt`.

## Pull Request Checklist

Before opening a pull request, verify:

- [ ] Changes are scoped and intentional
- [ ] Related source README has been updated
- [ ] New dependencies are documented in the correct requirements file
- [ ] Source folder includes `requirements.txt`, `start.sh`, and `start.bat`
- [ ] Startup scripts auto-create and use `<tool-root>/.venv`
- [ ] Basic manual verification was performed
- [ ] Logs/temp files are excluded from version control
- [ ] Root-level docs were updated if structure changed

## Source Onboarding Checklist

Use this checklist when adding a new source folder:

- [ ] Create source folder at repository root (example: `newSourceTool/`)
- [ ] Add source README with scope, requirements, run steps, and limitations
- [ ] Add `requirements.txt` (mandatory)
- [ ] Add `start.sh` and `start.bat` (mandatory)
- [ ] Ensure scripts auto-create and use `<tool-root>/.venv`
- [ ] Document output locations and logging behavior
- [ ] Add legal-use notice in source README
- [ ] Link the new source in root `README.md`

## Suggested Source README Template

Use this section order for consistency:

1. Scope
2. Folder Layout
3. Features
4. Requirements
5. Installation
6. Quick Start
7. CLI/API Reference
8. Output and Logs
9. Troubleshooting
10. Known Limitations
11. Legal Notice

## Development Workflow

1. Create a feature branch.
2. Make focused changes.
3. Validate the tool locally.
4. Update documentation.
5. Open a pull request with test/verification notes.

## Reporting Issues

When reporting a bug, include:

- source folder name
- exact command or API request
- expected behavior
- actual behavior
- relevant logs/error output
- OS and Python version
