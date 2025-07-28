#!/usr/bin/env python
from core.browser import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_rule1_cf_bypass():
    """Test different methods to bypass Rule1 CF protection"""
    driver = get_driver()
    
    try:
        print("🔍 Testing Rule1 CF bypass methods...")
        
        # Method 1: Direct navigation with longer wait
        print("\n📍 Method 1: Direct navigation")
        driver.get("https://ruleonetoolbox.com/explore/stocks")
        time.sleep(10)  # Wait for CF check
        
        # Check if we can find search input
        try:
            search_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//input[contains(@placeholder, "Search")]'))
            )
            print("✅ Method 1: Search input found - CF bypassed")
            
            # Test search with a ticker
            search_input.clear()
            search_input.send_keys("AAPL")
            search_input.submit()
            time.sleep(5)
            
            if "/ticker/" in driver.current_url:
                print("✅ Method 1: Successfully navigated to ticker page")
                return True
            else:
                print("⚠️ Method 1: Search didn't work")
                
        except Exception as e:
            print(f"❌ Method 1 failed: {e}")
        
        # Method 2: Try different user agent
        print("\n📍 Method 2: Different approach")
        driver.execute_script("window.location.reload();")
        time.sleep(15)  # Longer wait
        
        try:
            # Look for any sign we're past CF
            WebDriverWait(driver, 30).until(
                lambda d: "ruleonetoolbox.com" in d.current_url and "challenge" not in d.current_url.lower()
            )
            print("✅ Method 2: Passed CF challenge")
            return True
        except:
            print("❌ Method 2: Still blocked by CF")
        
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_rule1_cf_bypass()