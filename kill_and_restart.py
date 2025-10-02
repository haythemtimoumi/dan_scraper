#!/usr/bin/env python
import os
import signal
import subprocess
import time

def kill_scraper_processes():
    """Kill any running scraper processes"""
    try:
        # Kill any python processes running scraper scripts
        subprocess.run(['pkill', '-f', 'scrape_rule1_only.py'], check=False)
        subprocess.run(['pkill', '-f', 'chrome'], check=False)
        subprocess.run(['pkill', '-f', 'chromedriver'], check=False)
        print("✅ Killed existing scraper processes")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Error killing processes: {e}")

def restart_scraper():
    """Restart the Rule1 scraper"""
    try:
        print("🔄 Restarting Rule1 scraper...")
        subprocess.run(['python', 'scrape_rule1_only.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Scraper failed: {e}")
    except KeyboardInterrupt:
        print("\n⚠️ Scraper interrupted by user")

if __name__ == "__main__":
    kill_scraper_processes()
    restart_scraper()