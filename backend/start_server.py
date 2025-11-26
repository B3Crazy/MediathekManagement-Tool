#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start the MediathekManagement-Tool Backend API Server
"""

import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
