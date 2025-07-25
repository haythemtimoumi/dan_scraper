import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Import the browser module from the core package
from core.browser import get_driver
from utils.source_tracker import save_ticker_source

def login_to_stockscores(headless=True):
    """
    Log in to StockScores.com using credentials.
    
    Args:
        headless (bool): Whether to run in headless mode (default: True for Ubuntu VPS)
    
    Returns:
        driver: The browser driver instance after successful login
    """
    # Initialize the browser (headless mode by default for Ubuntu VPS)
    driver = get_driver(headless=headless)
    
    try:
        # Navigate to the login page
        print("Navigating to StockScores login page...")
        driver.get("https://www.stockscores.com/my-account/")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-form-username"))
        )
        
        # Enter login credentials
        print("Entering login credentials...")
        username_field = driver.find_element(By.ID, "login-form-username")
        password_field = driver.find_element(By.ID, "login-form-password")
        
        # Clear fields and enter credentials
        username_field.clear()
        username_field.send_keys("Stock@tundraeng.com")
        
        password_field.clear()
        password_field.send_keys("56Stingray#")
        
        # Click the login button
        print("Submitting login form...")
        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()
        
        # Wait for successful login
        print("Waiting for login to complete...")
        time.sleep(5)  # Give it some time to process the login
        
        # Navigate to the scanner page
        print("Navigating to the scanner page...")
        driver.get("https://www.stockscores.com/market-scan/scanner/")
        
        # Wait for the scanner page to load
        print("Waiting for scanner page to load...")
        time.sleep(5)  # Give it time to load the page
        
        # Find and click the scan dropdown
        print("Looking for the scan dropdown...")
        try:
            # First find and click the scan dropdown
            dropdown_button = driver.find_element(By.CSS_SELECTOR, ".btn.dropdown-toggle.btn-default")
            print("Found dropdown button, clicking it...")
            dropdown_button.click()
            time.sleep(2)  # Wait for dropdown to open
            
            # Find and click the Stockscores Basic Long option
            print("Looking for 'Stockscores Basic Long' option...")
            option = driver.find_element(By.XPATH, "//span[contains(text(), 'Stockscores Basic Long')]")
            print("Found the option, clicking it...")
            option.click()
            print("Successfully selected 'Stockscores Basic Long'")
            time.sleep(2)  # Wait for selection to apply
            
            # Now select 'NASDAQ' from the exchange dropdown
            print("Selecting 'NASDAQ' from exchange dropdown...")
            exchange_dropdown = driver.find_element(By.CSS_SELECTOR, "button[data-id='exchange']")
            exchange_dropdown.click()
            time.sleep(1)  # Wait for dropdown to open
            
            # Select NASDAQ option
            nasdaq_option = driver.find_element(By.XPATH, "//span[text()='NASDAQ']")
            nasdaq_option.click()
            print("Successfully selected 'NASDAQ' exchange")
            time.sleep(1)  # Wait for selection to apply
            
            # Now select market cap options using direct JavaScript
            print("Selecting market cap options...")
            
            # Use JavaScript to directly set the selections without clicking the dropdown
            # This will deselect 'All' and only select Mid-cap and Large-cap
            script = """
            // Get the select element
            var select = document.getElementById('marketcap');
            
            // Deselect all options first
            for (var i = 0; i < select.options.length; i++) {
                select.options[i].selected = false;
            }
            
            // Select only Mid-cap and Large-cap
            for (var i = 0; i < select.options.length; i++) {
                if (select.options[i].value === 'mid' || select.options[i].value === 'large') {
                    select.options[i].selected = true;
                }
            }
            
            // Trigger change event
            var event = new Event('change');
            select.dispatchEvent(event);
            
            // Update the Bootstrap Select UI
            $(select).selectpicker('refresh');
            """
            
            driver.execute_script(script)
            print("Selected only 'Mid-cap' and 'Large-cap' options")
            time.sleep(1)
            
            # Set MaxResult to 999
            print("Setting MaxResult to 999...")
            max_result_input = driver.find_element(By.NAME, "MaxResult")
            max_result_input.clear()
            max_result_input.send_keys("999")
            print("Successfully set MaxResult to 999")
            
            # Wait a moment for the page to update after selection
            time.sleep(3)
            
            # Find and click the Run Market Scan button
            print("Looking for 'Run Market Scan' button...")
            run_scan_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Run Market Scan')]")
            print("Found the button, clicking it...")
            run_scan_button.click()
            print("Successfully clicked 'Run Market Scan' button")
            
            # Wait for the results to load
            print("Waiting for scan results to load...")
            time.sleep(10)  # Give it time to load the results
            
            # Scrape ticker symbols from the results table
            print("Scraping ticker symbols from results...")
            ticker_elements = driver.find_elements(By.XPATH, "//td[@align='left']/a[contains(@href, '/charts/charts/?ticker=')]")
            
            tickers = []
            for element in ticker_elements:
                ticker = element.text.strip()
                if ticker:
                    tickers.append(ticker)
            
            # Save tickers to a file with source tracking
            if tickers:
                print(f"Found {len(tickers)} ticker symbols")
                with open("stock_list_tickers.txt", "w") as f:
                    for ticker in tickers:
                        f.write(f"{ticker}\n")
                        save_ticker_source(ticker, 'stock_list')
                print("Saved ticker symbols to 'stock_list_tickers.txt'")
            
            else:
                print("No ticker symbols found in the results")
                # Create empty file to avoid errors
                with open("stock_list_tickers.txt", "w") as f:
                    pass
        except Exception as e:
            print(f"Error selecting from dropdown: {e}")
            print("Taking screenshot for debugging...")
            driver.save_screenshot("stockscores_debug.png")
            print("Screenshot saved as 'stockscores_debug.png'")
        
        return driver
    
    except Exception as e:
        print(f"Error during login process: {e}")
        driver.quit()
        return None

if __name__ == "__main__":
    # Run the login function if script is executed directly
    driver = login_to_stockscores()
    
    if driver:
        print("Successfully logged in to StockScores.com")
        # Keep the browser open for a moment to see the result
        time.sleep(5)
        driver.quit()
    else:
        print("Failed to log in to StockScores.com")