#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start the MediathekManagement-Tool Backend API Server
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    from package_updater import PackageUpdater
    from browser_manager import BrowserCookieManager
    
    # Check for updates on startup
    logging.info("=== MediathekManagement-Tool Backend Starting ===")
    
    updates_installed = PackageUpdater.check_and_update_packages()
    
    if updates_installed:
        logging.info("Updates installed. Restarting...")
        PackageUpdater.restart_application()
    
    # Detect browser
    cookie_mgr = BrowserCookieManager()
    browser = cookie_mgr.detect_browser()
    
    if not browser:
        logging.warning(cookie_mgr.get_user_message())
        print("\n" + cookie_mgr.get_user_message())
    else:
        logging.info(f"Browser detected: {browser}")
    
    # Start server
    import uvicorn
    logging.info("Starting API server on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
