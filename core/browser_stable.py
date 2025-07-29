import os
import sys
import tempfile
import time
import shutil
import psutil
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Disable WebDriver Manager logs for faster startup
logging.getLogger('WDM').setLevel(logging.WARNING)

load_dotenv()

def kill_chrome_processes():
    """Kill any existing Chrome processes to prevent conflicts"""
    try:
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and ('chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower()):
                    proc.terminate()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if killed_count > 0:
            time.sleep(2)  # Give more time for processes to terminate
            # Force kill any remaining processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and ('chrome' in proc.info['name'].lower() or 'chromedriver' in proc.info['name'].lower()):
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(1)
            print(f"Killed {killed_count} Chrome processes")
    except Exception as e:
        print(f"Warning: Could not kill Chrome processes: {e}")

def get_stable_driver(headless=True):
    """
    Initialize and return a stable Chrome browser instance.
    """
    # Clean up old temp directories first
    cleanup_temp_directories()
    try:
        print("Initializing stable Chrome browser...")
        
        # First kill any existing Chrome processes
        kill_chrome_processes()
        
        # Create options without user-data-dir to avoid conflicts
        options = Options()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-sync")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--enable-automation")
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")
        import random
        debug_port = random.randint(9222, 9999)
        options.add_argument(f"--remote-debugging-port={debug_port}")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--incognito")
        
        if headless:
            options.add_argument("--headless=new")
        
        temp_dir = None  # No temp dir needed
        
        # Try multiple driver paths
        driver_paths = [
            "/root/.wdm/drivers/chromedriver/linux64/138.0.7204.168/chromedriver-linux64/chromedriver",
            ChromeDriverManager().install()
        ]
        
        service = None
        for path in driver_paths:
            if os.path.exists(path):
                try:
                    service = Service(path)
                    break
                except Exception as e:
                    print(f"Failed to use driver at {path}: {e}")
                    continue
        
        if service is None:
            raise Exception("No valid ChromeDriver found")
        
        # Try to create driver with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver = webdriver.Chrome(service=service, options=options)
                print("Stable Chrome session started successfully")
                print(f"Browser version: {driver.capabilities.get('browserVersion', 'Unknown')}")
                print("Using incognito mode (no user data directory)")
                return driver
            except Exception as e:
                if "user data directory is already in use" in str(e) and attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed, retrying with new directory...")
                    # Clean up current temp dir if it exists
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    kill_chrome_processes()
                    time.sleep(2)
                    
                    # Create new options object without user-data-dir
                    options = Options()
                    options.add_argument("--window-size=1920,1080")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-infobars")
                    options.add_argument("--disable-browser-side-navigation")
                    options.add_argument("--disable-background-timer-throttling")
                    options.add_argument("--disable-backgrounding-occluded-windows")
                    options.add_argument("--disable-client-side-phishing-detection")
                    options.add_argument("--disable-default-apps")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--disable-hang-monitor")
                    options.add_argument("--disable-popup-blocking")
                    options.add_argument("--disable-prompt-on-repost")
                    options.add_argument("--disable-renderer-backgrounding")
                    options.add_argument("--disable-sync")
                    options.add_argument("--metrics-recording-only")
                    options.add_argument("--no-first-run")
                    options.add_argument("--safebrowsing-disable-auto-update")
                    options.add_argument("--enable-automation")
                    options.add_argument("--password-store=basic")
                    options.add_argument("--use-mock-keychain")
                    debug_port = random.randint(9222, 9999)
                    options.add_argument(f"--remote-debugging-port={debug_port}")
                    options.add_argument("--disable-web-security")
                    options.add_argument("--disable-features=VizDisplayCompositor")
                    options.add_argument("--incognito")
                    
                    if headless:
                        options.add_argument("--headless=new")
                    
                    temp_dir = None
                else:
                    raise e
        
    except Exception as e:
        print(f"Failed to initialize stable Chrome browser: {e}")
        # Clean up temp directory if it was created
        if 'temp_dir' in locals() and temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
        # Kill any Chrome processes that might have started
        kill_chrome_processes()
        sys.exit(1)

def cleanup_temp_directories():
    """Clean up old Chrome temp directories"""
    try:
        temp_base = tempfile.gettempdir()
        for item in os.listdir(temp_base):
            if item.startswith('chrome_') and os.path.isdir(os.path.join(temp_base, item)):
                try:
                    shutil.rmtree(os.path.join(temp_base, item), ignore_errors=True)
                except:
                    pass
    except Exception as e:
        print(f"Warning: Could not clean temp directories: {e}")