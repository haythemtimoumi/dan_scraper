#!/usr/bin/env python3
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_chrome():
    print("Testing minimal Chrome setup...")
    
    # Create unique temp directory
    temp_dir = tempfile.mkdtemp(prefix="chrome_test_")
    print(f"Using temp dir: {temp_dir}")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={temp_dir}")
    options.add_argument("--remote-debugging-port=0")
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome started successfully!")
        
        driver.get("https://httpbin.org/ip")
        print("Page loaded:", driver.title)
        
        driver.quit()
        print("Test completed successfully")
        return True
        
    except Exception as e:
        print(f"Chrome test failed: {e}")
        return False

if __name__ == "__main__":
    test_chrome()