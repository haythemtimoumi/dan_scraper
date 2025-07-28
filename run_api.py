#!/usr/bin/env python
"""
Run the Monthly Ticker Task Scheduler API
"""

import os
import sys

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

if __name__ == "__main__":
    try:
        import uvicorn
        from api.app import app
        
        print("Starting Monthly Ticker Task Scheduler API...")
        print("Dashboard will be available at: http://localhost:8000/dashboard")
        print("API documentation at: http://localhost:8000/docs")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("Error: uvicorn not found. Install with: pip install uvicorn fastapi")
        sys.exit(1)