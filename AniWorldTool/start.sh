#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/requirements.txt"
MAIN_FILE="$ROOT_DIR/AniLoad.py"

find_python() {
	if command -v python3 >/dev/null 2>&1; then
		if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
			echo "python3"
			return 0
		fi
	fi

	if command -v python >/dev/null 2>&1; then
		if python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
			echo "python"
			return 0
		fi
	fi

	return 1
}

install_with_pip() {
	local venv_python="$1"
	"$venv_python" -m pip install --upgrade pip

	if [[ -s "$REQ_FILE" ]]; then
		"$venv_python" -m pip install -r "$REQ_FILE"
	else
		# Fallback when requirements file is still empty.
		"$venv_python" -m pip install aniworld rich
	fi
}

echo "== AniLoad starter =="

PYTHON_CMD="$(find_python)"
if [[ -z "$PYTHON_CMD" ]]; then
	echo "Error: Python 3.8+ was not found in PATH."
	exit 1
fi

if [[ ! -f "$MAIN_FILE" ]]; then
	echo "Error: AniLoad.py was not found in $ROOT_DIR"
	exit 1
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
	echo "Creating virtual environment in $VENV_DIR"
	"$PYTHON_CMD" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

echo "Installing dependencies"
install_with_pip "$VENV_PYTHON"

echo "Starting AniLoad"
cd "$ROOT_DIR" || exit 1
exec "$VENV_PYTHON" "$MAIN_FILE" "$@"
