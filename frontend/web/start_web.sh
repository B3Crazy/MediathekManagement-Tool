#!/bin/bash
echo "Starting MediathekManagement-Tool Web Frontend"
echo "=============================================="
echo ""

cd "$(dirname "$0")"

echo "IMPORTANT: Make sure the backend server is running!"
echo "Start it with: backend/start_backend.sh"
echo ""
echo "Starting web server on http://localhost:8080"
echo ""

python3 -m http.server 8080 --bind 0.0.0.0
