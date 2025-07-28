#!/usr/bin/env python
"""
Test script to verify Chrome browser configuration works on Windows
"""

import sys
import time
from core.browser import get_driver

def test_browser():
    """Test if the browser configuration works properly"""
    print("Testing Chrome browser configuration...")
    
    try:
        # Test visible browser
        print("Testing visible browser...")
        driver = get_driver(headless=False)
        
        # Navigate to a test page
        print("Navigating to test page...")
        driver.get("https://www.google.com")
        
        # Wait a bit to see the browser
        print("Waiting 5 seconds to verify browser is visible...")
        time.sleep(5)
        
        # Get page title
        title = driver.title
        print(f"Page title: {title}")
        
        # Close browser
        driver.quit()
        print("Browser test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"Browser test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_browser()
    if not success:
        sys.exit(1)
    print("All tests passed!")