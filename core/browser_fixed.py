import os
import sys
import time
import subprocess
import shutil
import glob
from dotenv import load_dotenv
import undetected_chromedriver as uc

load_dotenv()

def kill_chrome_processes():
    """Kill all Chrome processes"""
    try:
        subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
        subprocess.run(["fuser", "-k", "9222/tcp"], capture_output=True)
        subprocess.run(["fuser", "-k", "9223/tcp"], capture_output=True)
        time.sleep(2)
    except:
        pass

def clear_chrome_cache():
    """Clear Chrome cache and temp files"""
    try:
        cache_paths = [
            "~/.cache/google-chrome", 
            "~/.config/google-chrome", 
            "~/.local/share/undetected_chromedriver"
        ]
        for path in cache_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                shutil.rmtree(expanded, ignore_errors=True)
        
        for tmp_path in glob.glob("/tmp/chrome_*") + glob.glob("/tmp/.com.google.Chrome.*"):
            shutil.rmtree(tmp_path, ignore_errors=True)
    except:
        pass

def get_chrome_options(headless=True):
    """Get fresh Chrome options"""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    if headless:
        options.add_argument("--headless=new")
    
    return options

def get_driver(headless=True, clear_cache=False):
    """Initialize Chrome driver with proper error handling"""
    
    if clear_cache:
        print("Clearing browser cache...")
        kill_chrome_processes()
        clear_chrome_cache()
        print("Cache cleared successfully")
    
    print("Initializing Chrome browser...")
    
    # Always kill existing processes first
    kill_chrome_processes()
    
    try:
        options = get_chrome_options(headless)
        chrome_version = int(os.getenv("CHROME_VERSION", "138"))
        
        driver = uc.Chrome(options=options, version_main=chrome_version)
        
        print("Chrome session started successfully")
        print("Browser version:", driver.capabilities.get("browserVersion", "Unknown"))
        
        return driver
        
    except Exception as e:
        print(f"Failed to initialize Chrome browser: {e}")
        print("Trying fallback method...")
        
        # Fallback: try without version specification
        try:
            kill_chrome_processes()
            time.sleep(3)
            options = get_chrome_options(headless)
            driver = uc.Chrome(options=options)
            print("Chrome session started with fallback method")
            return driver
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            sys.exit(1)