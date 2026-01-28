#!/bin/bash
echo "Starting MediathekManagement-Tool Desktop Frontend"
echo "=================================================="
echo ""

cd "$(dirname "$0")"
cd ../..

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

echo "Installing/Updating dependencies..."
pip install -r frontend/desktop/requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "IMPORTANT: Make sure the backend server is running!"
    echo "Start it with: backend/start_backend.sh"
    echo ""
    echo "Starting desktop application..."
    echo ""
    cd frontend/desktop
    python mediathek_desktop.py
else
    echo ""
    echo "Error installing dependencies!"
    read -p "Press Enter to continue..."
fi
