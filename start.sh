#!/bin/bash
echo "========================================"
echo "MediathekManagement-Tool - Quick Start"
echo "========================================"
echo ""
echo "This script will start both the backend server"
echo "and the desktop frontend application."
echo ""

cd "$(dirname "$0")"

# Setup virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
        echo ""
        echo "Error creating virtual environment!"
        echo "Please run: apt install python3-venv python3-full"
        echo "Or use the version-specific command: apt install python3.12-venv"
        read -p "Press Enter to continue..."
        exit 1
    fi
    echo "Virtual environment created successfully!"
fi

# Activate virtual environment
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: venv/bin/activate not found!"
    echo "Please delete the venv folder and run this script again."
    echo "Command: rm -rf venv"
    read -p "Press Enter to continue..."
    exit 1
fi

source "$VENV_DIR/bin/activate"
echo "Using virtual environment: $VIRTUAL_ENV"

echo "Step 1/3: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "Error installing dependencies!"
    read -p "Press Enter to continue..."
    exit 1
fi

echo ""
echo "Step 2/3: Starting backend server..."
BASEDIR="$(pwd)"
gnome-terminal -- bash -c "cd '$BASEDIR' && source venv/bin/activate && cd backend && python start_server.py; exec bash" 2>/dev/null || \
xterm -e "cd '$BASEDIR' && source venv/bin/activate && cd backend && python start_server.py" 2>/dev/null || \
x-terminal-emulator -e bash -c "cd '$BASEDIR' && source venv/bin/activate && cd backend && python start_server.py; exec bash" 2>/dev/null || \
konsole -e bash -c "cd '$BASEDIR' && source venv/bin/activate && cd backend && python start_server.py; exec bash" 2>/dev/null || \
(echo "Could not open terminal. Starting backend in background..." && cd backend && "$BASEDIR/venv/bin/python" start_server.py &)

echo ""
echo "Waiting for backend to start (5 seconds)..."
sleep 5

echo ""
echo "Step 3/3: Starting web interface..."
cd frontend/web
echo ""
echo "Opening browser at http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

# Try to open browser
xdg-open http://localhost:8080 2>/dev/null || \
firefox http://localhost:8080 2>/dev/null || \
chromium http://localhost:8080 2>/dev/null || \
google-chrome http://localhost:8080 2>/dev/null &

python -m http.server 8080 --bind 0.0.0.0

echo ""
echo "Server stopped."
read -p "Press Enter to continue..."
