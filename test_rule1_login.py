#!/usr/bin/env python
"""
Test Rule1 login with stable browser
"""
from core.browser_stable import get_stable_driver
from core.auth_rule1 import Rule1Auth
import time

def test_rule1_login():
    print("Testing Rule1 login with stable browser...")
    driver = get_stable_driver(headless=True)
    
    try:
        auth = Rule1Auth(driver)
        print("Attempting login...")
        result = auth.login(auto_verify=False)  # Use manual verification for testing
        print(f"Login result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    test_rule1_login()