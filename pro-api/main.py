#!/usr/bin/env python
"""
Main scraper controller that runs either sequential or daily process based on config
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append('/root/dan_scraper')

CONFIG_FILE = '/root/dan_scraper/pro-api/scraper_config.json'

def load_config():
    """Load scraper configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config
        return {'script': 'run_sequential_scraping'}

def run_main():
    """Run the configured scraper script"""
    config = load_config()
    script = config.get('script', 'run_sequential_scraping')
    
    print(f"Starting main scraper at {datetime.now()}")
    print(f"Running script: {script}")
    
    if script == 'run_sequential_scraping':
        from run_sequential_scraping import run_sequential_scraping
        run_sequential_scraping()
    elif script == 'daily_process':
        from daily_process import run_daily_process
        run_daily_process()
    else:
        print(f"Unknown script: {script}")
        sys.exit(1)

if __name__ == "__main__":
    run_main()