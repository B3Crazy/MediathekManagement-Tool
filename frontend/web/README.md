# MediathekManagement-Tool Web Frontend

## Running the Web Frontend

The web frontend is a static HTML/CSS/JavaScript application that communicates with the backend API.

### Option 1: Using Python's built-in HTTP server

```bash
cd frontend/web
python -m http.server 8080
```

Then open http://localhost:8080 in your browser.

### Option 2: Using any web server

You can use any web server to serve the files:
- Live Server (VS Code extension)
- nginx
- Apache
- Node.js http-server

## Important

Make sure the backend server is running on http://localhost:8000 before using the web frontend!

Start the backend with:
```bash
cd backend
python start_server.py
```

or

```bash
backend\start_backend.bat
```
