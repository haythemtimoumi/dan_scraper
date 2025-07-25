import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def extract_calculator_data(driver, ticker, wait_time=10):
    """
    A more robust function to extract calculator data (sticker price and last price)
    from the Rule1 calculator page.
    
    Args:
        driver: Selenium WebDriver instance
        ticker: Ticker symbol being processed
        wait_time: Maximum wait time in seconds
        
    Returns:
        dict: Dictionary containing sticker_price and last_price, or None if extraction fails
    """
    print(f"🔍 Extracting calculator data for {ticker}...")
    
    # Create a WebDriverWait instance
    wait = WebDriverWait(driver, wait_time)
    
    # Check if we're on the calculator page
    if "calculators" not in driver.current_url:
        print(f"⚠️ Not on calculator page for {ticker}, attempting to navigate directly")
        try:
            # Try to construct and navigate to the calculator URL
            base_url = driver.current_url.split("/ticker/")[0]
            ticker_part = driver.current_url.split("/ticker/")[1].split("/")[0] if "/ticker/" in driver.current_url else ticker
            calculator_url = f"{base_url}/ticker/{ticker_part}/analysis/calculators"
            print(f"Attempting to navigate to: {calculator_url}")
            driver.get(calculator_url)
            time.sleep(5)
        except Exception as url_error:
            print(f"⚠️ Error navigating to calculator URL: {url_error}")
    
    # Wait for calculator results to load
    try:
        # Wait for the calculator results container
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "calculator-results")]'))
        )
        print(f"✅ Calculator results container found for {ticker}")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"⚠️ Calculator results container not found: {e}")
        # Try to proceed anyway
    
    # Extract sticker price
    sticker_price = None
    sticker_selectors = [
        # Direct path to sticker price value
        '//div[contains(@class, "calculator-results__values-box")][./div[contains(text(), "Sticker Price")]]/div[contains(@class, "calculator-results__value")]',
        # Look for the label then get the sibling
        '//div[contains(@class, "calculator-results__label") and contains(text(), "Sticker Price")]/following-sibling::div',
        # Look for the value-numbers class
        '//div[contains(@class, "calculator-results__value-numbers")]',
        # Most generic selector
        '//div[contains(@class, "calculator-results__value")]'
    ]
    
    for selector in sticker_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            sticker_price = element.text.strip()
            print(f"✅ Found sticker price with selector: {selector}")
            break
        except:
            continue
    
    if not sticker_price:
        print(f"⚠️ Could not find sticker price for {ticker} with any selector")
        # Try to get it from page source as a last resort
        try:
            page_source = driver.page_source
            import re
            sticker_match = re.search(r'Sticker Price.*?currency-symbol[^>]*>\$(.*?)<', page_source, re.DOTALL)
            if sticker_match:
                sticker_price = f"${sticker_match.group(1)}"
                print(f"✅ Extracted sticker price from page source: {sticker_price}")
        except Exception as e:
            print(f"⚠️ Failed to extract sticker price from page source: {e}")
    
    # Extract last price
    last_price = None
    last_price_selectors = [
        # Direct path to last price value
        '//div[contains(@class, "calculator-results__values-box")][./div[contains(text(), "Last Price")]]/div[contains(@class, "calculator-results__value")]',
        # Look for the label then get the sibling
        '//div[contains(@class, "calculator-results__label") and contains(text(), "Last Price")]/following-sibling::div',
        # Look for the value-lastnumbers class
        '//div[contains(@class, "calculator-results__value-lastnumbers")]',
        # Most generic selector
        '//div[contains(@class, "calculator-results__value")]'
    ]
    
    for selector in last_price_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            last_price = element.text.strip()
            print(f"✅ Found last price with selector: {selector}")
            break
        except:
            continue
    
    if not last_price:
        print(f"⚠️ Could not find last price for {ticker} with any selector")
        # Try to get it from page source as a last resort
        try:
            page_source = driver.page_source
            import re
            last_match = re.search(r'Last Price.*?currency-symbol-lastPrice[^>]*>\$(.*?)<', page_source, re.DOTALL)
            if last_match:
                last_price = f"${last_match.group(1)}"
                print(f"✅ Extracted last price from page source: {last_price}")
        except Exception as e:
            print(f"⚠️ Failed to extract last price from page source: {e}")
    
    # Return the results
    if sticker_price or last_price:
        result = {
            'sticker_price': sticker_price if sticker_price else "N/A",
            'last_price': last_price if last_price else "N/A"
        }
        print(f"✅ Extracted calculator data for {ticker}: {result}")
        return result
    else:
        print(f"❌ Failed to extract any calculator data for {ticker}")
        return None