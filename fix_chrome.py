#!/usr/bin/env python3
import os
import subprocess
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def fix_chrome_and_run():
    """Fix Chrome issues and run the scraper"""
    
    print("Fixing Chrome configuration...")
    
    # 1. Kill all Chrome processes aggressively
    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "chromedriver"], capture_output=True)
    time.sleep(2)
    
    # 2. Remove all Chrome-related files and directories
    chrome_dirs = [
        "~/.config/google-chrome",
        "~/.cache/google-chrome", 
        "/tmp/.com.google.Chrome*",
        "/tmp/.org.chromium.Chromium*",
        "/tmp/chrome_*",
        "/tmp/tmp*chrome*"
    ]
    
    for dir_pattern in chrome_dirs:
        subprocess.run(f"rm -rf {dir_pattern}", shell=True, capture_output=True)
    
    # 3. Create a completely unique temp directory
    unique_dir = tempfile.mkdtemp(prefix=f"chrome_fix_{int(time.time())}_")
    os.chmod(unique_dir, 0o755)
    
    print(f"Using unique Chrome directory: {unique_dir}")
    
    # 4. Set up Chrome options with the unique directory
    options = Options()
    options.add_argument(f"--user-data-dir={unique_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome fixed and initialized successfully!")
        
        # Test basic functionality
        driver.get("https://www.google.com")
        print(f"Chrome is working! Title: {driver.title}")
        
        driver.quit()
        
        # Clean up the temp directory
        subprocess.run(f"rm -rf {unique_dir}", shell=True, capture_output=True)
        
        print("Chrome is now ready. You can run your scraper.")
        return True
        
    except Exception as e:
        print(f"Chrome fix failed: {e}")
        # Clean up the temp directory
        subprocess.run(f"rm -rf {unique_dir}", shell=True, capture_output=True)
        return False

if __name__ == "__main__":
    if fix_chrome_and_run():
        print("Running the scraper...")
        os.system("python3 dan_watchlist_to_db.py")
    else:
        print("Chrome fix failed. Please reboot the system.")