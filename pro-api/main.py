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
    elif script == 'scrape_all_active_ticker':
        from scrape_all_active_ticker import run_active_process
        run_active_process()
    else:
        print(f"Unknown script: {script}")
        sys.exit(1)

if __name__ == "__main__":
    run_main()
    
    # Create daily backup to S3 after scraping
    print("\n🗄️ Creating daily database backup...")
    try:
        from daily_backup_to_s3 import daily_backup_to_s3
        daily_backup_to_s3()
        print("✅ Daily backup completed")
    except Exception as e:
        print(f"❌ Daily backup failed: {e}")