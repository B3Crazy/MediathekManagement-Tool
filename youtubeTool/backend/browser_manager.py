#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Cookie Manager and PO Token Handler
Handles browser detection, cookie management, and download strategies
"""

import os
import sys
import subprocess
import time
import logging
from typing import Optional, Dict, List


class BrowserCookieManager:
    """Manage browser cookie detection and PO token"""
    
    _instance = None
    _detected_browser: Optional[str] = None
    _po_token: Optional[str] = None
    _last_detection_time: float = 0
    _detection_cache_duration: int = 300  # 5 minutes (reduced from 1 hour)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def detect_browser(self, force_redetect: bool = False) -> Optional[str]:
        """Detect which browser has accessible cookies"""
        current_time = time.time()
        
        # Use cached result if available and not expired
        if not force_redetect and self._detected_browser and \
           (current_time - self._last_detection_time) < self._detection_cache_duration:
            logging.debug(f"Using cached browser: {self._detected_browser}")
            return self._detected_browser
        
        # Browser priority: Chrome, Edge, Firefox, Brave, Opera
        browsers = ['chrome', 'edge', 'firefox', 'brave', 'opera', 'chromium']
        
        logging.info("Detecting available browser cookies...")
        
        for browser in browsers:
            try:
                # Fast test: just check if cookies can be accessed
                test_cmd = [
                    sys.executable, "-m", "yt_dlp",
                    "--cookies-from-browser", browser,
                    "--print", "%(id)s",
                    "--skip-download",
                    "--no-warnings",
                    "--quiet",
                    "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video
                ]
                
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    timeout=5,  # Reduced from 15s to 5s
                    text=True
                )
                
                # Success if we can extract video ID
                if result.returncode == 0 and 'jNQXAC9IVRw' in result.stdout:
                    self._detected_browser = browser
                    self._last_detection_time = current_time
                    logging.info(f"✓ Browser cookies available: {browser}")
                    return browser
                    
            except subprocess.TimeoutExpired:
                logging.debug(f"Browser {browser} check timed out")
                continue
            except Exception as e:
                logging.debug(f"Browser {browser} check failed: {e}")
                continue
        
        logging.warning("⚠ No browser cookies available - downloads may fail!")
        logging.warning("Please login to YouTube in Chrome, Edge, or Firefox")
        self._detected_browser = None
        self._last_detection_time = current_time
        return None
    
    def get_po_token(self) -> Optional[str]:
        """Get PO token if available (for advanced bot-protection bypass)"""
        return self._po_token
    
    def set_po_token(self, token: str):
        """Manually set PO token"""
        self._po_token = token
        logging.info("PO token set manually")
    
    def get_download_args(self, attempt: int = 1) -> Dict[str, List[str]]:
        """Get download arguments based on available authentication (uses cached browser info)"""
        # Use cached browser info - don't call detect_browser() again
        browser = self._detected_browser
        po_token = self.get_po_token()
        
        args = {
            "cookies": [],
            "client": [],
            "po_token": [],
            "ipv4": [],
            "extra": [],
            "description": ""
        }
        
        # Strategy based on attempt number
        # OPTIMIZED: Start with default strategy (fastest, works without cookies)
        if attempt == 1:
            # Strategy 1: Default (works without cookies - fastest!)
            args["description"] = "Default (no special client)"
            
        elif attempt <= 3 and browser:
            # Strategy 2-3: Browser cookies + iOS client
            args["cookies"] = ["--cookies-from-browser", browser]
            args["client"] = ["--extractor-args", "youtube:player_client=ios"]
            args["ipv4"] = ["--force-ipv4"]
            args["description"] = f"Browser cookies ({browser}) + iOS client"
            
        elif attempt <= 5 and browser:
            # Strategy 4-5: Browser cookies + TV client
            args["cookies"] = ["--cookies-from-browser", browser]
            args["client"] = ["--extractor-args", "youtube:player_client=tv"]
            args["ipv4"] = ["--force-ipv4"]
            args["description"] = f"Browser cookies ({browser}) + TV client"
            
        elif attempt <= 7:
            # Strategy 6-7: TV client without cookies
            args["client"] = ["--extractor-args", "youtube:player_client=tv"]
            args["ipv4"] = ["--force-ipv4"]
            args["description"] = "TV client (no cookies)"
            
        elif attempt <= 9 and browser:
            # Strategy 8-9: Browser cookies + Web client
            args["cookies"] = ["--cookies-from-browser", browser]
            args["client"] = ["--extractor-args", "youtube:player_client=web"]
            args["description"] = f"Browser cookies ({browser}) + Web client"
            
        else:
            # Strategy 10: Web client without cookies
            args["client"] = ["--extractor-args", "youtube:player_client=web"]
            args["description"] = "Web client (no cookies)"
        
        # Add PO token if available (works with any strategy)
        if po_token:
            args["po_token"] = ["--extractor-args", f"youtube:po_token={po_token}"]
            args["description"] += " + PO token"
        
        # Add retry parameters for robustness
        args["extra"] = [
            "--retries", "3",
            "--fragment-retries", "5",
            "--extractor-retries", "3",
        ]
        
        return args
    
    def get_user_message(self) -> str:
        """Get user-friendly message about browser status"""
        # Use cached browser info
        browser = self._detected_browser
        
        if browser:
            return f"✓ Using {browser.capitalize()} cookies for authentication"
        else:
            return """
⚠ Keine Browser-Cookies gefunden!

Für zuverlässige YouTube-Downloads:
1. Öffnen Sie Chrome, Edge oder Firefox
2. Melden Sie sich bei YouTube an
3. Versuchen Sie den Download erneut

Das Tool nutzt dann automatisch Ihre Browser-Cookies.
"""
