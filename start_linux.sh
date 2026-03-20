#!/usr/bin/env bash

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

print_header() {
  echo "========================================"
  echo " MediathekManagement-Tool  Quick Start"
  echo "========================================"
  echo
}

pause() {
  echo
  read -r -p "Press Enter to continue..." _
}

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo
    echo "Stopping backend (PID $BACKEND_PID)..."
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

venv_has_pip() {
  [[ -x "$VENV_PYTHON" ]] && "$VENV_PYTHON" -m pip --version >/dev/null 2>&1
}

create_venv() {
  "$PYTHON_CMD" -m venv "$VENV_DIR"
}

install_linux_venv_support() {
  local py_major_minor
  py_major_minor="$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

  if ! command -v apt-get >/dev/null 2>&1; then
    return 1
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update && (sudo apt-get install -y "python${py_major_minor}-venv" || sudo apt-get install -y python3-venv)
  elif [[ "$EUID" -eq 0 ]]; then
    apt-get update && (apt-get install -y "python${py_major_minor}-venv" || apt-get install -y python3-venv)
  else
    return 1
  fi
}

print_header

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo " !! Do not run this script as root."
  echo " Run it as your normal user so downloads use your user account."
  exit 1
fi

# ============================================================
# STEP 1  Find a working Python interpreter
# ============================================================
echo "[1/5] Checking Python installation..."

PYTHON_CMD=""

if command -v python3 >/dev/null 2>&1; then
  if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    PYTHON_CMD="python3"
  fi
fi

if [[ -z "$PYTHON_CMD" ]] && command -v python >/dev/null 2>&1; then
  if python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    PYTHON_CMD="python"
  fi
fi

if [[ -z "$PYTHON_CMD" ]]; then
  echo
  echo " !! Python 3.8+ was not found."
  echo " Install it, then re-run this script."
  echo " Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
  echo " Fedora:        sudo dnf install python3 python3-pip"
  echo " Arch:          sudo pacman -S python python-pip"
  pause
  exit 1
fi

PY_VERSION="$($PYTHON_CMD --version 2>&1)"
echo "   Found: $PY_VERSION"

# ============================================================
# STEP 2  Create virtual environment
# ============================================================
echo
echo "[2/5] Setting up virtual environment (.venv)..."

if [[ -x "$VENV_PYTHON" ]] && ! venv_has_pip; then
  echo "   Existing .venv is incomplete (pip missing). Recreating..."
  rm -rf "$VENV_DIR"
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "   Creating .venv ..."
  if ! create_venv; then
    echo "   venv creation failed. Trying to install missing venv support..."
    if install_linux_venv_support && create_venv; then
      :
    else
      echo
      echo " !! Could not create virtual environment."
      echo " Install Python venv support (e.g. python3-venv) and retry."
      pause
      exit 1
    fi
  fi
  echo "   Done."
else
  echo "   Already exists and looks healthy."
fi

# ============================================================
# STEP 3  Install dependencies into venv
# ============================================================
echo
echo "[3/5] Installing Python dependencies..."

if ! venv_has_pip; then
  "$VENV_PYTHON" -m ensurepip --upgrade >/dev/null 2>&1 || true
fi

"$VENV_PYTHON" -m pip install --upgrade pip --quiet
if "$VENV_PYTHON" -m pip install -r "$ROOT/requirements.txt"; then
  echo "   All dependencies installed."
else
  echo
  echo " !! Some packages failed to install. The app may not work correctly."
  pause
fi

# ============================================================
# STEP 4  Check / auto-install ffmpeg
# ============================================================
echo
echo "[4/5] Checking ffmpeg..."

if command -v ffmpeg >/dev/null 2>&1; then
  echo "   ffmpeg found."
else
  echo "   ffmpeg not found. Trying automatic installation..."
  FF_INSTALL_OK=0

  if command -v apt-get >/dev/null 2>&1; then
    if sudo apt-get update && sudo apt-get install -y ffmpeg; then
      FF_INSTALL_OK=1
    fi
  elif command -v dnf >/dev/null 2>&1; then
    if sudo dnf install -y ffmpeg; then
      FF_INSTALL_OK=1
    fi
  elif command -v pacman >/dev/null 2>&1; then
    if sudo pacman -Sy --noconfirm ffmpeg; then
      FF_INSTALL_OK=1
    fi
  elif command -v zypper >/dev/null 2>&1; then
    if sudo zypper --non-interactive install ffmpeg; then
      FF_INSTALL_OK=1
    fi
  fi

  if [[ "$FF_INSTALL_OK" -eq 1 ]] && command -v ffmpeg >/dev/null 2>&1; then
    echo "   ffmpeg installed."
  else
    echo "   WARNING: ffmpeg still not available. Video downloads may fail."
  fi
fi

# ============================================================
# STEP 5  Launch application
# ============================================================
echo
echo "[5/5] Starting application..."
echo

BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"

trap cleanup EXIT INT TERM

(
  cd "$BACKEND_DIR" || exit 1
  exec "$VENV_PYTHON" start_server.py
) &
BACKEND_PID=$!

echo "   Waiting for backend to start (5 seconds)..."
sleep 5

echo "   Opening web frontend at http://localhost:8080"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://localhost:8080" >/dev/null 2>&1 || true
elif command -v gio >/dev/null 2>&1; then
  gio open "http://localhost:8080" >/dev/null 2>&1 || true
fi

cd "$FRONTEND_DIR" || exit 1
echo "   Frontend server running. Press Ctrl+C to stop."
echo
"$VENV_PYTHON" -m http.server 8080 --bind 0.0.0.0

echo
echo "   Application stopped."
