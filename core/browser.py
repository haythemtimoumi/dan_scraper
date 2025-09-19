import os
import sys
from dotenv import load_dotenv
import undetected_chromedriver as uc

load_dotenv()

def get_driver(headless=True, clear_cache=False):
    """
    Initialize Chrome browser with fallback to regular selenium if undetected fails
    """
    import subprocess
    import time
    
    # Kill existing Chrome processes
    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
    time.sleep(2)
    
    # Try undetected Chrome first
    try:
        print("Trying undetected Chrome...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-login-animations")
        options.add_argument("--disable-motion-blur")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--no-first-run")
        
        if headless:
            options.add_argument("--headless=new")
        
        driver = uc.Chrome(options=options, version_main=None)
        print("✅ Undetected Chrome initialized successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Undetected Chrome failed: {e}")
        print("Falling back to regular Selenium Chrome...")
        
        # Fallback to regular selenium
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--remote-debugging-port=9222")
            
            if headless:
                options.add_argument("--headless=new")
            
            # Try to find Chrome binary
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium"
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    options.binary_location = chrome_path
                    break
            
            driver = webdriver.Chrome(options=options)
            print("✅ Regular Selenium Chrome initialized successfully")
            return driver
            
        except Exception as e2:
            print(f"❌ Regular Chrome also failed: {e2}")
            raise Exception(f"Both undetected and regular Chrome failed: {e}, {e2}")