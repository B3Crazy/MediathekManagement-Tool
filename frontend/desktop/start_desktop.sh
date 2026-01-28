#!/bin/bash
echo "Starting MediathekManagement-Tool Desktop Frontend"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

echo "Installing/Updating dependencies..."
python3 -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "IMPORTANT: Make sure the backend server is running!"
    echo "Start it with: backend/start_backend.sh"
    echo ""
    echo "Starting desktop application..."
    echo ""
    python3 mediathek_desktop.py
else
    echo ""
    echo "Error installing dependencies!"
    read -p "Press Enter to continue..."
fi
