#!/usr/bin/env python
"""
Hourly scraper controller that runs either hourly_scraping or scrape_all_active_ticker_hourly based on config
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append('/root/dan_scraper')

CONFIG_FILE = '/root/dan_scraper/pro-api/hourly_scraper_config.json'

def load_config():
    """Load hourly scraper configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config
        return {'script': 'hourly_scraping'}

def run_hourly_main():
    """Run the configured hourly scraper script"""
    config = load_config()
    script = config.get('script', 'hourly_scraping')
    
    print(f"Starting hourly scraper at {datetime.now()}")
    print(f"Running script: {script}")
    
    if script == 'hourly_scraping':
        from hourly_scraping import run_hourly_scraping
        run_hourly_scraping()
    elif script == 'scrape_all_active_ticker_hourly':
        from scrape_all_active_ticker_hourly import run_active_hourly_process
        run_active_hourly_process()
    else:
        print(f"Unknown script: {script}")
        sys.exit(1)

if __name__ == "__main__":
    run_hourly_main()