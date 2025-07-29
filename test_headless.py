#!/usr/bin/env python
"""
Simple test to verify headless Chrome works
"""
from core.browser import get_driver
import time

def test_headless():
    print("Testing headless Chrome...")
    driver = get_driver(headless=True)
    
    try:
        driver.get("https://www.google.com")
        print(f"✅ Successfully loaded Google")
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    test_headless()