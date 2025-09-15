#!/usr/bin/env python
import subprocess
import time
import os

# Kill any existing Chrome processes
subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
time.sleep(2)

# Test basic Chrome functionality
try:
    print("Testing Chrome installation...")
    result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
    print(f"Chrome version: {result.stdout.strip()}")
    
    print("\nTesting Chrome headless mode...")
    result = subprocess.run([
        "google-chrome", 
        "--headless", 
        "--no-sandbox", 
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--dump-dom",
        "https://www.google.com"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print("✅ Chrome headless test successful")
    else:
        print(f"❌ Chrome headless test failed: {result.stderr}")
        
except Exception as e:
    print(f"❌ Chrome test failed: {e}")

# Test undetected-chromedriver
try:
    print("\nTesting undetected-chromedriver...")
    import undetected_chromedriver as uc
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=0")
    
    driver = uc.Chrome(options=options, version_main=138)
    driver.get("https://www.google.com")
    print("✅ Undetected Chrome test successful")
    driver.quit()
    
except Exception as e:
    print(f"❌ Undetected Chrome test failed: {e}")