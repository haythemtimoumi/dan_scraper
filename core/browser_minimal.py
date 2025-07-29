import os
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def get_minimal_driver(headless=True):
    """Get minimal Chrome driver with absolute minimal configuration"""
    
    # Kill all Chrome processes aggressively
    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "chromedriver"], capture_output=True)
    time.sleep(3)
    
    # Remove any Chrome lock files
    subprocess.run(["rm", "-rf", "/tmp/.com.google.Chrome*"], capture_output=True)
    subprocess.run(["rm", "-rf", "/tmp/.org.chromium.Chromium*"], capture_output=True)
    
    options = Options()
    
    # Absolutely minimal options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    if headless:
        options.add_argument("--headless=new")
    
    # Try to use system chromedriver first
    chromedriver_paths = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/root/.wdm/drivers/chromedriver/linux64/138.0.7204.168/chromedriver-linux64/chromedriver"
    ]
    
    service = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            service = Service(path)
            break
    
    if service is None:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("Minimal Chrome driver initialized successfully")
        return driver
    except Exception as e:
        print(f"Failed to initialize minimal Chrome: {e}")
        raise e