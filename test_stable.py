#!/usr/bin/env python
"""
Test stable Chrome browser
"""
from core.browser_stable import get_stable_driver
import time

def test_stable():
    print("Testing stable Chrome...")
    driver = get_stable_driver(headless=True)
    
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
    test_stable()