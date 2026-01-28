#!/bin/bash
echo "Starting MediathekManagement-Tool Backend Server"
echo "================================================"
echo ""

cd "$(dirname "$0")"

echo "Installing/Updating dependencies..."
python3 -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "Starting server on http://localhost:8000"
    echo "API documentation available at http://localhost:8000/docs"
    echo ""
    python3 start_server.py
else
    echo ""
    echo "Error installing dependencies!"
    read -p "Press Enter to continue..."
fi
