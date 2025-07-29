#!/usr/bin/env python
"""
Simple test script to verify browser functionality
"""

import subprocess
import time
import undetected_chromedriver as uc

def kill_all_chrome():
    """Kill all Chrome processes"""
    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
    subprocess.run(["fuser", "-k", "9222/tcp"], capture_output=True)
    subprocess.run(["fuser", "-k", "9223/tcp"], capture_output=True)
    time.sleep(2)

def test_browser():
    """Test basic browser functionality"""
    kill_all_chrome()
    
    try:
        print("Testing basic Chrome setup...")
        
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--single-process")
        
        driver = uc.Chrome(options=options, version_main=138)
        
        print("✅ Browser started successfully")
        
        # Test basic navigation
        driver.get("https://www.google.com")
        print(f"✅ Navigation successful: {driver.title}")
        
        driver.quit()
        print("✅ Browser closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_browser()
    if success:
        print("🎉 Browser test passed! You can now run your scrapers.")
    else:
        print("💥 Browser test failed. Check your Chrome installation.")