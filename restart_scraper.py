#!/usr/bin/env python
"""
Emergency restart script to clean up stuck processes and restart scraping
"""

import subprocess
import time
import os
import signal

def cleanup_processes():
    """Kill all Chrome and Python scraper processes"""
    print("🧹 Cleaning up stuck processes...")
    
    # Kill Chrome processes
    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
    
    # Kill stuck Python scraper processes
    subprocess.run(["pkill", "-9", "-f", "scrape_all_active_ticker"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "stockscores_scraper"], capture_output=True)
    
    # Clear temp files
    import glob
    import shutil
    for tmp_path in glob.glob("/tmp/chrome_*") + glob.glob("/tmp/.com.google.Chrome.*"):
        try:
            shutil.rmtree(tmp_path, ignore_errors=True)
        except:
            pass
    
    print("✅ Cleanup completed")
    time.sleep(3)

def restart_scraping():
    """Start the robust scraper"""
    print("🚀 Starting robust scraper...")
    os.system("python /root/dan_scraper/robust_active_scraper.py")

if __name__ == "__main__":
    cleanup_processes()
    restart_scraping()