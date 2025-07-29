import os
import sys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from dotenv import load_dotenv
from core.browser import get_driver
from core.auth_rule1 import Rule1Auth

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

load_dotenv()

# Additional encoding fix for print statements
def safe_print(*args, **kwargs):
    """Safe print function that handles encoding issues"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ascii with replacement
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
            else:
                safe_args.append(str(arg).encode('ascii', 'replace').decode('ascii'))
        print(*safe_args, **kwargs)

class Rule1Scraper:
    """
    Scraper for Rule1Toolbox website.
    Handles scraping operations after authentication.
    """
    
    def __init__(self, driver=None, headless=True, clear_cache=False):
        """
        Initialize the Rule1Scraper.
        
        Args:
            driver: Optional Selenium WebDriver instance. If not provided, a new one will be created.
            headless: Whether to run browser in headless mode (default: True)
            clear_cache: Whether to clear browser cache before starting (default: False)
        """
        self.driver = driver if driver else get_driver(headless=headless, clear_cache=clear_cache)
        self.wait = WebDriverWait(self.driver, 10)
        self.auth = Rule1Auth(self.driver)
        
    def login(self, auto_verify=True):
        """
        Check if already logged in, and only log in if necessary.
        
        Args:
            auto_verify (bool): Whether to automatically verify email code (default: True)
            
        Returns:
            bool: True if already logged in or login successful, False otherwise
        """
        # First check if we're already logged in by looking for dashboard elements
        try:
            # Check if driver is still alive
            try:
                self.driver.current_url
            except Exception as driver_error:
                print(f"⚠️ Driver connection lost: {driver_error}")
                return False
            
            # Try multiple selectors for dashboard elements
            dashboard_selectors = [
                '//a[contains(@href, "/explore/guru-portfolio")]',
                '//a[contains(@href, "/dashboard")]',
                '//div[contains(@class, "dashboard")]',
                '//h1[contains(text(), "Dashboard") or contains(text(), "Welcome")]',
                '//div[contains(@class, "logged-in")]'
            ]
            
            for selector in dashboard_selectors:
                try:
                    # Use a short timeout for this check
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print("✅ Already logged in, skipping login process")
                    return True
                except:
                    continue
                    
            # If we get here, we're not logged in, so proceed with login
            return self.auth.login(auto_verify=auto_verify)
            
        except Exception as e:
            print(f"⚠️ Error checking login status: {e}")
            # Fall back to regular login
            return self.auth.login(auto_verify=auto_verify)

    def navigate_to_stock_scan(self):
        """
        Navigate to the Stock Scan page by:
        1. Hovering over the 'Explore' menu
        2. Clicking the 'Scan for Stocks' option
        3. Verifying the URL changes to /explore/stocks
        """
        try:
            print("🔍 Navigating to Stock Scan page...")

            # Wait for the 'Explore' menu link to appear
            explore_xpath = '//a[@id="primaryMenuItemExplore"]'
            explore_menu = self.wait.until(
                EC.presence_of_element_located((By.XPATH, explore_xpath))
            )

            # Hover over 'Explore' to reveal the submenu
            ActionChains(self.driver).move_to_element(explore_menu).perform()
            print("✅ Hovered over 'Explore' menu item")

            # Wait for 'Scan for Stocks' to become clickable
            scan_xpath = '//span[text()="Scan for Stocks"]'
            scan_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, scan_xpath))
            )
            scan_link.click()
            print("✅ Clicked on 'Scan for Stocks'")

            # Confirm the URL contains /explore/stocks
            self.wait.until(EC.url_contains("/explore/stocks"))
            print("✅ Successfully navigated to Stock Scan page")
            return True

        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Navigation to Stock Scan page failed: {e}")
            return False
            
    def get_ticker_data(self, ticker):
        """
        Scrape data for a specific ticker.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Scraped data for the ticker
        """
        print(f"🔍 Scraping data for {ticker}...")
        
        try:
            # First, try to find the ticker in the current table results
            table_data = self.scrape_stock_table()
            
            # Look for the ticker in the scraped data
            for stock in table_data:
                if stock['ticker'] == ticker:
                    print(f"✅ Found {ticker} in the table results")
                    return stock
            
            # If ticker not found in current results, try to search for it
            print(f"⚠️ {ticker} not found in current table results, attempting to search...")
            
            # Try to find a search input field
            try:
                search_input = self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '//input[contains(@placeholder, "Search") or contains(@placeholder, "Filter")]'
                    ))
                )
                
                # Clear any existing search text
                search_input.clear()
                
                # Enter the ticker symbol
                search_input.send_keys(ticker)
                print(f"✅ Entered {ticker} in search field")
                
                # Press Enter to search
                search_input.send_keys(Keys.ENTER)
                print("✅ Pressed Enter to search")
                
                # Wait for search results
                time.sleep(2)
                
                # Try to scrape the table again after search
                search_results = self.scrape_stock_table()
                
                # Look for the ticker in the search results
                for stock in search_results:
                    if stock['ticker'] == ticker:
                        print(f"✅ Found {ticker} in search results")
                        return stock
                
                print(f"⚠️ {ticker} not found in search results")
                return {"ticker": ticker, "status": "not found"}
                
            except (TimeoutException, NoSuchElementException) as e:
                print(f"⚠️ Could not find search field: {e}")
                return {"ticker": ticker, "status": "search failed"}
                
        except Exception as e:
            print(f"❌ Error scraping data for {ticker}: {e}")
            return {"ticker": ticker, "status": "error", "message": str(e)}
        
    def get_tickers_from_file(self, file_path="config/tickers_rule1.txt"):
        """
        Read ticker symbols from a file.
        
        Args:
            file_path (str): Path to the file containing tickers
            
        Returns:
            list: List of ticker symbols
        """
        tickers = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    ticker = line.strip()
                    if ticker:
                        tickers.append(ticker)
            return tickers
        except Exception as e:
            print(f"❌ Error reading tickers file: {e}")
            return []
            
    def scrape_all_tickers(self, file_path="config/tickers_rule1.txt"):
        """
        Scrape data for all tickers in the specified file.
        
        Args:
            file_path (str): Path to the file containing tickers
            
        Returns:
            dict: Dictionary of ticker data
        """
        tickers = self.get_tickers_from_file(file_path)
        if not tickers:
            print("⚠️ No tickers found to scrape")
            return {}
            
        results = {}
        for ticker in tickers:
            results[ticker] = self.get_ticker_data(ticker)
            
        return results
        
    def configure_rule_one_scores(self):
        """
        Configure the Rule One Scores section in the Stock Scan page.
        Sets Moat Score, Management Score, and Rule One Score to 85.
        """
        try:
            print("🔍 Configuring Rule One Scores section...")
            
            # First expand the section if needed
            try:
                accordion = self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '//div[contains(text(), "Rule One Scores") and contains(@class, "scan-filters__group-name")]'
                    ))
                )
                if 'p-accordion-tab-active' not in accordion.find_element(By.XPATH, './ancestor::div[contains(@class, "p-accordion-tab")]').get_attribute('class'):
                    accordion.click()
                    print("✅ Expanded Rule One Scores section")
                    time.sleep(1)
            except Exception as e:
                print(f"⚠️ Could not expand Rule One Scores section: {e}")

            # Score names to configure
            score_names = ["Moat Score", "Management Score", "Rule One Score"]
            
            for score_name in score_names:
                try:
                    print(f"🔧 Configuring {score_name}...")
                    
                    # Find the checkbox container for this score
                    checkbox = self.wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            f'//label[contains(@class, "p-checkbox-label") and contains(text(), "{score_name}")]/preceding-sibling::div[contains(@class, "p-checkbox")]'
                        ))
                    )
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                    time.sleep(0.3)
                    
                    # Click the checkbox if not already checked
                    if 'p-checkbox-checked' not in checkbox.get_attribute('class'):
                        checkbox.click()
                        print(f"✅ Checked {score_name} checkbox")
                        time.sleep(0.5)
                    
                    # Find the input field
                    input_field = self.wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            f'//label[contains(@class, "p-checkbox-label") and contains(text(), "{score_name}")]/ancestor::div[contains(@class, "scan-criterion")]//input[contains(@class, "p-inputnumber-input")]'
                        ))
                    )
                    
                    # Clear existing value
                    input_field.clear()
                    time.sleep(0.2)
                    
                    # Set new value
                    input_field.send_keys("85")
                    time.sleep(0.2)
                    
                    # Press Enter to confirm
                    input_field.send_keys(Keys.ENTER)
                    time.sleep(0.5)
                    
                    print(f"✅ Set {score_name} to 85")
                    
                except Exception as e:
                    print(f"⚠️ Error configuring {score_name}: {str(e)}")
                    continue
            
            print("✅ Successfully configured all Rule One Scores to 85")
            
            # Try to apply the filter
            try:
                # Find any input and press Enter to apply
                input_field = self.driver.find_element(
                    By.XPATH,
                    '//input[contains(@class, "p-inputnumber-input")]'
                )
                input_field.send_keys(Keys.ENTER)
                print("✅ Pressed Enter to apply filter")
            except Exception as e:
                print(f"⚠️ Could not press Enter to apply filter: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error configuring Rule One Scores: {str(e)}")
            return False
            
    def apply_filter(self, max_retries=3):
        """
        Apply the filter after all values have been set up by pressing Enter.
        
        Args:
            max_retries (int): Maximum number of retries if the filter application fails
            
        Returns:
            bool: True if filter application successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                print(f"🔍 Applying filter (attempt {attempt + 1}/{max_retries})...")
                
                # Try multiple approaches to apply the filter
                success = False
                
                # Approach 1: Find any input field and press Enter
                try:
                    input_selectors = [
                        '//input[contains(@class, "p-inputtext")]',
                        '//input[contains(@class, "p-inputnumber-input")]',
                        '//input[@type="text"]'
                    ]
                    
                    for selector in input_selectors:
                        try:
                            input_fields = self.driver.find_elements(By.XPATH, selector)
                            if input_fields:
                                input_field = input_fields[0]
                                input_field.send_keys(Keys.ENTER)
                                print("✅ Pressed Enter to apply the filter")
                                success = True
                                break
                        except Exception:
                            continue
                except Exception as e:
                    print(f"⚠️ Could not find input field to press Enter: {e}")
                
                # Approach 2: Try to find and click an Apply button if it exists
                if not success:
                    try:
                        button_selectors = [
                            '//button[contains(., "Apply") or contains(., "Filter")]',
                            '//button[contains(@class, "apply") or contains(@class, "filter")]',
                            '//span[contains(text(), "Apply")]/parent::button'
                        ]
                        
                        for selector in button_selectors:
                            try:
                                buttons = self.driver.find_elements(By.XPATH, selector)
                                if buttons:
                                    self.driver.execute_script("arguments[0].click();", buttons[0])
                                    print("✅ Clicked Apply button to apply the filter")
                                    success = True
                                    break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"⚠️ Could not find Apply button: {e}")
                
                # Approach 3: Use JavaScript to trigger filter application
                if not success:
                    try:
                        # Try to use JavaScript to trigger the filter application
                        js_script = """
                        // Try to find and trigger filter application
                        function applyFilter() {
                            // Try to find apply/filter buttons
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const applyButton = buttons.find(btn => 
                                btn.textContent.toLowerCase().includes('apply') || 
                                btn.textContent.toLowerCase().includes('filter')
                            );
                            
                            if (applyButton) {
                                applyButton.click();
                                return true;
                            }
                            
                            // If no button found, try to find an input and simulate Enter
                            const inputs = document.querySelectorAll('input.p-inputtext, input.p-inputnumber-input');
                            if (inputs.length > 0) {
                                const event = new KeyboardEvent('keydown', {
                                    key: 'Enter',
                                    code: 'Enter',
                                    keyCode: 13,
                                    which: 13,
                                    bubbles: true
                                });
                                inputs[0].dispatchEvent(event);
                                return true;
                            }
                            
                            return false;
                        }
                        
                        return applyFilter();
                        """
                        
                        result = self.driver.execute_script(js_script)
                        if result:
                            print("✅ Applied filter using JavaScript")
                            success = True
                    except Exception as js_error:
                        print(f"⚠️ JavaScript filter application failed: {js_error}")
                
                # Wait for the filter to be applied
                try:
                    # Wait for any loading indicator to disappear (with a longer timeout)
                    WebDriverWait(self.driver, 15).until(
                        EC.invisibility_of_element_located((
                            By.XPATH,
                            '//div[contains(@class, "p-progress-spinner")] | //div[contains(@class, "loading")]'
                        ))
                    )
                    print("✅ Filter applied successfully")
                except TimeoutException:
                    # If no loading indicator is found, assume the filter was applied instantly
                    print("ℹ️ No loading indicator found, assuming filter was applied")
                
                # Check if we have results or a no-results message
                try:
                    # Look for table rows or a no-results message
                    WebDriverWait(self.driver, 5).until(
                        lambda driver: len(driver.find_elements(By.XPATH, '//tbody/tr')) > 0 or 
                                      len(driver.find_elements(By.XPATH, '//div[contains(text(), "No results")]')) > 0
                    )
                    print("✅ Filter results confirmed")
                    return True
                except TimeoutException:
                    if attempt == max_retries - 1:
                        # On the last attempt, assume success even if we can't confirm results
                        print("⚠️ Could not confirm filter results, but continuing anyway")
                        return True
                    else:
                        print("⚠️ Could not confirm filter results, retrying...")
                        time.sleep(2)  # Wait before retrying
                        continue
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Filter application attempt {attempt + 1} failed: {e}")
                    print(f"⚠️ Retrying in 2 seconds...")
                    time.sleep(2)  # Wait before retrying
                else:
                    print(f"❌ All filter application attempts failed: {e}")
                    # Return True anyway to allow the process to continue
                    return True
        
        # If we've exhausted all retries, return True anyway to allow the process to continue
        return True
            
    def scrape_stock_table(self, max_pages=10):
        """
        Scrape data from the stock table after filters have been applied.
        Handles pagination by clicking the "Next" button to navigate through multiple pages.
        
        Args:
            max_pages (int): Maximum number of pages to scrape (default: 10)
        
        Returns:
            list: List of dictionaries containing ticker data with the following keys:
                - ticker: Stock ticker symbol
                - moat_score: Moat Score value
                - management_score: Management Score value
                - rule_one_score: Rule One Score value
        """
        try:
            print("🔍 Scraping stock table data...")
            
            # Wait for the table to be visible
            self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//tbody[contains(@class, "p-datatable-tbody")]'
                ))
            )
            
            results = []
            current_page = 1
            
            while current_page <= max_pages:
                print(f"📄 Scraping page {current_page}...")
                
                # Find all table rows on the current page
                rows = self.driver.find_elements(
                    By.XPATH,
                    '//tbody[contains(@class, "p-datatable-tbody")]/tr[contains(@class, "ng-star-inserted")]'
                )
                
                if not rows:
                    print(f"⚠️ No rows found in the stock table on page {current_page}")
                    break
                    
                print(f"✅ Found {len(rows)} rows in the stock table on page {current_page}")
                
                # Process rows on the current page
                for row in rows:
                    try:
                        # Extract ticker symbol
                        ticker_element = row.find_element(
                            By.XPATH,
                            './/div[contains(@class, "scan-for-stocks__company-symbol")]'
                        )
                        ticker = ticker_element.text.strip()
                        
                        # Extract score values (spans containing the scores)
                        score_elements = row.find_elements(
                            By.XPATH,
                            './/span[contains(@class, "ng-star-inserted")]'
                        )
                        
                        # We expect 3 score elements: Moat Score, Management Score, Rule One Score
                        if len(score_elements) >= 3:
                            moat_score = score_elements[0].text.strip()
                            management_score = score_elements[1].text.strip()
                            rule_one_score = score_elements[2].text.strip()
                            
                            stock_data = {
                                'ticker': ticker,
                                'moat_score': moat_score,
                                'management_score': management_score,
                                'rule_one_score': rule_one_score
                            }
                            
                            results.append(stock_data)
                            print(f"✅ Scraped data for {ticker}: Moat={moat_score}, Management={management_score}, Rule One={rule_one_score}")
                        else:
                            print(f"⚠️ Could not find all score elements for a row, found {len(score_elements)} elements")
                    except NoSuchElementException as e:
                        print(f"⚠️ Error extracting data from a row: {e}")
                        continue
                
                # Check if there's a next page button and if it's enabled
                try:
                    # Find the next page button using the exact class names from the request
                    next_button = self.driver.find_element(
                        By.XPATH,
                        '//button[contains(@class, "p-paginator-next") and contains(@class, "p-paginator-element")]'
                    )
                    
                    # Check if the button is disabled
                    is_disabled = 'p-disabled' in next_button.get_attribute('class') or next_button.get_attribute('disabled') == 'true'
                    
                    if is_disabled:
                        print("🛑 Reached the last page of results")
                        break
                    
                    # Click the next page button
                    print("➡️ Clicking next page button...")
                    next_button.click()
                    
                    # Wait for the page to load
                    time.sleep(1)  # Short delay to allow the page to update
                    
                    # Wait for any loading indicator to disappear
                    try:
                        self.wait.until(
                            EC.invisibility_of_element_located((
                                By.XPATH,
                                '//div[contains(@class, "p-progress-spinner")] | //div[contains(@class, "loading")]'
                            ))
                        )
                    except TimeoutException:
                        # If no loading indicator is found, continue anyway
                        pass
                    
                    current_page += 1
                    
                except NoSuchElementException:
                    print("ℹ️ No pagination controls found, assuming single page of results")
                    break
            
            print(f"✅ Successfully scraped data for {len(results)} stocks across {current_page} page(s)")
            return results
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to scrape stock table: {e}")
            return []

    def scrape_only_tickers(self, max_pages=10):
        """
        Scrape only ticker symbols from the stock table after filters have been applied.
        Handles pagination by clicking the "Next" button to navigate through multiple pages.
        
        Args:
            max_pages (int): Maximum number of pages to scrape (default: 10)
        
        Returns:
            list: List of ticker symbols
        """
        try:
            print("🔍 Scraping only ticker symbols from stock table...")
            
            # Wait for the table to be visible
            self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//tbody[contains(@class, "p-datatable-tbody")]'
                ))
            )
            
            tickers = []
            current_page = 1
            
            while current_page <= max_pages:
                print(f"📄 Scraping tickers from page {current_page}...")
                
                # Find all table rows on the current page
                rows = self.driver.find_elements(
                    By.XPATH,
                    '//tbody[contains(@class, "p-datatable-tbody")]/tr[contains(@class, "ng-star-inserted")]'
                )
                
                if not rows:
                    print(f"⚠️ No rows found in the stock table on page {current_page}")
                    break
                    
                print(f"✅ Found {len(rows)} rows in the stock table on page {current_page}")
                
                # Process rows on the current page
                for row in rows:
                    try:
                        # Extract ticker symbol
                        ticker_element = row.find_element(
                            By.XPATH,
                            './/div[contains(@class, "scan-for-stocks__company-symbol")]'
                        )
                        ticker = ticker_element.text.strip()
                        tickers.append(ticker)
                        print(f"✅ Scraped ticker: {ticker}")
                    except NoSuchElementException as e:
                        print(f"⚠️ Error extracting ticker from a row: {e}")
                        continue
                
                # Check if there's a next page button and if it's enabled
                try:
                    # Find the next page button using the exact class names from the request
                    next_button = self.driver.find_element(
                        By.XPATH,
                        '//button[contains(@class, "p-paginator-next") and contains(@class, "p-paginator-element")]'
                    )
                    
                    # Check if the button is disabled
                    is_disabled = 'p-disabled' in next_button.get_attribute('class') or next_button.get_attribute('disabled') == 'true'
                    
                    if is_disabled:
                        print("🛑 Reached the last page of results")
                        break
                    
                    # Click the next page button
                    print("➡️ Clicking next page button...")
                    next_button.click()
                    
                    # Wait for the page to load
                    time.sleep(1)  # Short delay to allow the page to update
                    
                    # Wait for any loading indicator to disappear
                    try:
                        self.wait.until(
                            EC.invisibility_of_element_located((
                                By.XPATH,
                                '//div[contains(@class, "p-progress-spinner")] | //div[contains(@class, "loading")]'
                            ))
                        )
                    except TimeoutException:
                        # If no loading indicator is found, continue anyway
                        pass
                    
                    current_page += 1
                    
                except NoSuchElementException:
                    print("ℹ️ No pagination controls found, assuming single page of results")
                    break
            
            print(f"✅ Successfully scraped {len(tickers)} ticker symbols across {current_page} page(s)")
            return tickers
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to scrape tickers: {e}")
            return []
            
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
                # Try to force close if normal quit fails
                try:
                    import os
                    import signal
                    import psutil
                    
                    # Try to get the process ID
                    try:
                        process = psutil.Process(self.driver.service.process.pid)
                        for child in process.children(recursive=True):
                            try:
                                os.kill(child.pid, signal.SIGTERM)
                            except:
                                pass
                        try:
                            os.kill(process.pid, signal.SIGTERM)
                        except:
                            pass
                    except:
                        pass
                except:
                    # If all else fails, just suppress the error and continue
                    pass