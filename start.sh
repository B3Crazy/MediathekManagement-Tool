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
    if [ $? -ne 0 ]; then
        echo ""
        echo "Error creating virtual environment!"
        echo "Please install python3-venv: sudo apt install python3-venv"
        read -p "Press Enter to continue..."
        exit 1
    fi
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

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
echo "Step 3/3: Starting desktop application..."
cd frontend/desktop
python mediathek_desktop.py

echo ""
echo "Application closed."
read -p "Press Enter to continue..."
