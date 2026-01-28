#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package Update Manager
Checks and updates required packages on startup
"""

import os
import sys
import subprocess
import logging


class PackageUpdater:
    """Manage package updates"""
    
    @staticmethod
    def check_and_update_packages() -> bool:
        """Check and update all required packages"""
        packages = ["yt-dlp", "fastapi", "uvicorn", "pydantic"]
        
        logging.info("Checking for package updates...")
        updates_needed = False
        
        for package in packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", package],
                    capture_output=True,
                    timeout=60,
                    text=True
                )
                
                if "Successfully installed" in result.stdout:
                    logging.info(f"✓ Updated {package}")
                    updates_needed = True
                else:
                    logging.info(f"✓ {package} already up-to-date")
                    
            except Exception as e:
                logging.error(f"Failed to update {package}: {e}")
        
        return updates_needed
    
    @staticmethod
    def restart_application():
        """Restart the application"""
        logging.info("Restarting application...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
