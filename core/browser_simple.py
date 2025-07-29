import os
import tempfile
import time
import shutil
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def kill_all_chrome():
    """Kill all Chrome processes"""
    os.system("pkill -f chrome 2>/dev/null || true")
    os.system("pkill -f chromedriver 2>/dev/null || true")
    time.sleep(2)

def get_simple_driver(headless=True):
    """Get a simple Chrome driver without user data directory conflicts"""
    
    # Kill any existing Chrome processes
    kill_all_chrome()
    
    # Create a unique temp directory
    temp_dir = tempfile.mkdtemp(prefix="chrome_selenium_")
    
    options = Options()
    
    # Use the temp directory
    options.add_argument(f"--user-data-dir={temp_dir}")
    
    # Basic required options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    if headless:
        options.add_argument("--headless=new")
    
    # Disable features that might cause conflicts
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-default-apps")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print(f"Simple Chrome driver initialized successfully with temp dir: {temp_dir}")
        
        # Store temp_dir in driver for cleanup
        driver._temp_dir = temp_dir
        
        return driver
    except Exception as e:
        # Clean up temp dir if driver creation failed
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Failed to initialize Chrome: {e}")
        raise e