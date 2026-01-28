#!/bin/bash
echo "========================================"
echo "MediathekManagement-Tool - Quick Start"
echo "========================================"
echo ""
echo "This script will start both the backend server"
echo "and the desktop frontend application."
echo ""

cd "$(dirname "$0")"

echo "Step 1/3: Installing dependencies..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "Error installing dependencies!"
    read -p "Press Enter to continue..."
    exit 1
fi

echo ""
echo "Step 2/3: Starting backend server..."
gnome-terminal -- bash -c "cd backend && python3 start_server.py; exec bash" 2>/dev/null || \
xterm -e "cd backend && python3 start_server.py" 2>/dev/null || \
x-terminal-emulator -e bash -c "cd backend && python3 start_server.py; exec bash" 2>/dev/null || \
konsole -e bash -c "cd backend && python3 start_server.py; exec bash" 2>/dev/null || \
(echo "Could not open terminal. Starting backend in background..." && cd backend && python3 start_server.py &)

echo ""
echo "Waiting for backend to start (5 seconds)..."
sleep 5

echo ""
echo "Step 3/3: Starting desktop application..."
cd frontend/desktop
python3 mediathek_desktop.py

echo ""
echo "Application closed."
read -p "Press Enter to continue..."
