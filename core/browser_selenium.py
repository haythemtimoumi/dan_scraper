import os
import sys
import time
import subprocess
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

load_dotenv()

def kill_chrome_processes():
    """Kill all Chrome processes"""
    try:
        subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
        time.sleep(2)
    except:
        pass

def get_driver(headless=True, clear_cache=False):
    """Initialize Chrome driver using standard selenium"""
    
    if clear_cache:
        print("Clearing browser processes...")
        kill_chrome_processes()
        print("Processes cleared")
    
    print("Initializing Chrome browser with selenium...")
    
    try:
        # Create unique temp directory
        temp_dir = tempfile.mkdtemp(prefix="chrome_scraper_")
        
        # Chrome options - minimal working set
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--remote-debugging-port=0")
        
        if headless:
            options.add_argument("--headless=new")
        
        # Use selenium's auto-managed chromedriver
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        print("Chrome session started successfully")
        print("Browser version:", driver.capabilities.get("browserVersion", "Unknown"))
        
        return driver
        
    except Exception as e:
        print(f"Failed to initialize Chrome browser: {e}")
        print("Please ensure Chrome and ChromeDriver are properly installed.")
        sys.exit(1)