import os
import time
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from core.browser import get_driver
from core.auth_rule1 import Rule1Auth
from dotenv import load_dotenv

load_dotenv()

class TickerSearcher:
    """
    Comprehensive ticker search system that:
    1. Combines tickers from multiple files
    2. Logs in to Rule1Toolbox (if not already logged in)
    3. Processes each ticker through search
    """
    
    def __init__(self, driver=None, csv_file="ticker_data.csv"):
        """
        Initialize the Rule1Scraper.
        
        Args:
            driver: Optional Selenium WebDriver instance. If not provided, a new one will be created.
            csv_file: Path to CSV file for saving data (default: ticker_data.csv)
        """
        self.driver = driver if driver else get_driver(headless=True)
        self.wait = WebDriverWait(self.driver, 15)  # Reduced from 30 to 15 seconds
        self.auth = Rule1Auth(self.driver)
        self.csv_file = csv_file
        
    def login(self, auto_verify=True):
        """
        Check if already logged in, and only log in if necessary.
        
        Args:
            auto_verify (bool): Whether to automatically verify email code (default: True)
            
        Returns:
            bool: True if already logged in or login successful, False otherwise
        """
        print("Checking login status...")
        
        # First check if we're already logged in by looking for dashboard elements
        try:
            # Navigate to a known page to check login status
            current_url = self.driver.current_url
            if "login" not in current_url.lower():
                # Try to access the explore page to test if we're logged in
                self.driver.get("https://ruleonetoolbox.com/explore/stocks")
                time.sleep(3)
            
            # Try multiple selectors for logged-in elements
            dashboard_selectors = [
                '//a[contains(@href, "/explore/guru-portfolio")]',
                '//a[contains(@href, "/dashboard")]', 
                '//input[@placeholder="Search for Stocks, Gurus"]',
                '//div[contains(@class, "dashboard")]',
                '//h1[contains(text(), "Dashboard") or contains(text(), "Welcome")]',
                '//div[contains(@class, "logged-in")]'
            ]
            
            # Check if already logged in with single timeout
            try:
                WebDriverWait(self.driver, 8).until(
                    lambda driver: any(
                        len(driver.find_elements(By.XPATH, selector)) > 0 
                        for selector in dashboard_selectors
                    )
                )
                print("✅ Already logged in, skipping login process")
                return True
            except TimeoutException:
                print("⚠️ Not logged in, proceeding with login...")
                pass
                    
            # If we get here, we're not logged in, so proceed with login
            print("Starting login process...")
            login_result = self.auth.login(auto_verify=auto_verify)
            print(f"Auth login result: {login_result}")
            
            # Double-check login success by trying to access a protected page
            if login_result:
                try:
                    self.driver.get("https://ruleonetoolbox.com/explore/stocks")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search for Stocks, Gurus"]'))
                    )
                    print("✅ Login verification successful - can access protected pages")
                    return True
                except TimeoutException:
                    print("⚠️ Login may have failed - cannot access protected pages")
                    return False
            
            return login_result
            
        except Exception as e:
            print(f"⚠️ Error checking login status: {e}")
            # Fall back to regular login
            try:
                login_result = self.auth.login(auto_verify=auto_verify)
                print(f"Fallback auth login result: {login_result}")
                return login_result
            except Exception as fallback_error:
                print(f"❌ Fallback login also failed: {fallback_error}")
                return False
    
    def combine_and_search_tickers(self, input_files=None, output_file="combined_tickers.txt"):
        """
        Main method that combines tickers and processes them
        Args:
            input_files: List of files to combine (defaults to common sources)
            output_file: Where to save combined tickers
        """
        # Set default input files if not provided
        if input_files is None:
            input_files = [
                "stock_list_tickers.txt",
                "scraped_tickers.txt",
                "guru_tickers.txt",
                "config/tickers_rule1.txt"
            ]
        
        # Combine ticker files first
        combined_count = self.combine_ticker_files(input_files, output_file)
        if combined_count == 0:
            print("⚠️ No tickers found to process")
            return False
            
        # Then process the combined file
        return self.process_ticker_file(output_file)
    
    def combine_ticker_files(self, input_files, output_file):
        """
        Combine tickers from multiple files into one and track sources
        Returns count of unique tickers found
        """
        from utils.source_tracker import save_ticker_source
        
        unique_tickers = set()
        
        for file_path in input_files:
            try:
                file_tickers = []
                with open(file_path, 'r') as f:
                    for line in f:
                        ticker = line.strip()
                        if ticker:
                            unique_tickers.add(ticker)
                            file_tickers.append(ticker)
                
                # Track source for tickers from this file
                if "config/tickers_rule1.txt" in file_path:
                    # Manual tickers
                    for ticker in file_tickers:
                        save_ticker_source(ticker, 'manual')
                    print(f"✅ Read {len(file_tickers)} manual tickers from {file_path}")
                elif "guru_tickers.txt" in file_path:
                    # Guru tickers (already tracked in guru_scraper.py as 'guru_list')
                    print(f"✅ Read {len(file_tickers)} guru_list tickers from {file_path}")
                elif "stock_list_tickers.txt" in file_path:
                    # StockScores tickers (already tracked in stockscores_login.py as 'stock_list')
                    print(f"✅ Read {len(file_tickers)} stock_list tickers from {file_path}")
                else:
                    # Rule1 tickers (already tracked in run_all_in_one.py)
                    print(f"✅ Read {len(file_tickers)} rule1 tickers from {file_path}")
                    
            except FileNotFoundError:
                print(f"⚠️ File not found: {file_path} - skipping")
                continue
            except Exception as e:
                print(f"⚠️ Error reading {file_path}: {e} - skipping")
                continue
        
        # Save combined file
        try:
            with open(output_file, 'w') as f:
                f.write("\n".join(sorted(unique_tickers)))
            print(f"✅ Saved {len(unique_tickers)} unique tickers to {output_file}")
            return len(unique_tickers)
        except Exception as e:
            print(f"❌ Failed to save combined tickers: {e}")
            return 0
    
    def process_ticker_file(self, input_file):
        """
        Process tickers from a file through the search system
        """
        if not self.login():
            print("❌ Login failed, cannot proceed with search")
            return False
            
        tickers = self._read_ticker_file(input_file)
        if not tickers:
            print("⚠️ No tickers found to process")
            return False
            
        print(f"🔍 Starting search for {len(tickers)} tickers...")
        
        # Store tickers list for navigation logic
        self._current_tickers = tickers
        
        success_count = 0
        for ticker in tickers:
            # Process the ticker
            if self._process_single_ticker(ticker):
                success_count += 1
            else:
                # If processing failed after all retries, reload the page before moving to the next ticker
                try:
                    print(f"🔄 All attempts failed for {ticker}. Reloading page before moving to next ticker...")
                    # Navigate to the stock scan page
                    self.driver.get("https://ruleonetoolbox.com/explore/stocks")
                    # Wait for page to load by checking for search input
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//input[contains(@placeholder, "Search for Stocks")]'))
                    )
                    
                    # Check if we need to log in again
                    try:
                        # Quick check if we're logged in
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/explore")]'))
                        )
                    except TimeoutException:
                        print("⚠️ May need to log in again after page reload")
                        if not self.login():
                            print("❌ Failed to log in again after page reload")
                except Exception as reload_error:
                    print(f"⚠️ Error during page reload after failed attempts: {reload_error}")
        
        print(f"✅ Finished processing - {success_count}/{len(tickers)} successful")
        return success_count > 0
    
    def _read_ticker_file(self, file_path):
        """Read tickers from a file"""
        try:
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ Error reading ticker file: {e}")
            return []
    
    def _process_single_ticker(self, ticker, max_retries=3):
        """Process a single ticker through search and scrape data"""
        """Process a single ticker through search and scrape data"""
        for attempt in range(max_retries):
            try:
                print(f"\n🔍 Processing {ticker} (attempt {attempt+1}/{max_retries})...")
                
                # Always navigate to search page for each ticker (except first attempt of first ticker)
                try:
                    print(f"🔄 Navigating to fresh search page for {ticker}...")
                    # Navigate to the stock scan page
                    self.driver.get("https://ruleonetoolbox.com/explore/stocks")
                    # Wait for search input to be available and page to be fully loaded
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Search for Stocks, Gurus"]'))
                    )
                    # Wait for page to be ready
                    WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Search for Stocks, Gurus"]'))
                    )
                    print(f"✅ Search page loaded for {ticker}")
                except Exception as reload_error:
                    print(f"⚠️ Error navigating to search page: {reload_error}")
                
                # Find and clear search input using the exact selector
                try:
                    search_input = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            '//input[@placeholder="Search for Stocks, Gurus"]'
                        ))
                    )
                except TimeoutException:
                    print("⚠️ Could not find search input, checking if we need to log in again...")
                    # Check if we need to log in again
                    if not self.login():
                        print("❌ Failed to log in again")
                        continue
                    # Try to find the search input again
                    search_input = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            '//input[@placeholder="Search for Stocks, Gurus"]'
                        ))
                    )
                
                search_input.clear()
                # Wait for input to be cleared
                WebDriverWait(self.driver, 3).until(
                    lambda driver: driver.find_element(By.XPATH, '//input[@placeholder="Search for Stocks, Gurus"]').get_attribute('value') == ''
                )
                
                # Enter ticker and submit
                search_input.send_keys(ticker)
                search_input.send_keys(Keys.ENTER)
                print(f"✅ Search submitted for {ticker}")
                
                # Wait for URL to actually change to the new ticker
                try:
                    # Store current URL before search
                    old_url = self.driver.current_url
                    
                    # Wait for URL to change AND contain ticker info
                    def url_changed_to_ticker(driver):
                        current = driver.current_url
                        return ("/ticker/" in current and 
                               current != old_url and
                               (ticker.upper() in current.upper() or 
                                any(exchange in current for exchange in ["NYS:", "NAS:", "AMEX:"])))
                    
                    WebDriverWait(self.driver, 15).until(url_changed_to_ticker)
                    
                    # Capture the exact URL we get after search
                    ticker_url = self.driver.current_url
                    print(f"Captured URL after search: {ticker_url}")
                    
                    # Extract the base part (everything before /company/brief or /analysis/)
                    if '/company/brief' in ticker_url:
                        base_ticker_url = ticker_url.replace('/company/brief', '')
                    elif '/analysis/' in ticker_url:
                        base_ticker_url = ticker_url.split('/analysis/')[0]
                    else:
                        base_ticker_url = ticker_url
                    
                    print(f"Base ticker URL: {base_ticker_url}")
                    
                except TimeoutException:
                    ticker_url = self.driver.current_url
                    print(f"⚠️ URL didn't change properly after search: {ticker_url}")
                    
                    # Check if we're still on scan page - ticker might not exist in Rule1
                    if "scan-for-stocks" in ticker_url or "explore/stocks" in ticker_url:
                        print(f"⚠️ {ticker} not found in Rule1Toolbox (staying on scan page)")
                        return False
                    
                    print(f"⚠️ Expected ticker: {ticker}, but URL shows different ticker")
                    
                    # Try clicking search button if Enter didn't work
                    try:
                        print("🔄 Trying to click search button instead...")
                        search_button = self.driver.find_element(By.XPATH, '//i[@class="pi pi-search"]')
                        search_button.click()
                        time.sleep(3)
                        
                        # Check if URL changed now
                        ticker_url = self.driver.current_url
                        if "/ticker/" in ticker_url and ticker_url != old_url:
                            print(f"✅ Search button worked: {ticker_url}")
                        elif "scan-for-stocks" in ticker_url:
                            print(f"⚠️ {ticker} not found in Rule1Toolbox after search button click")
                            return False
                        else:
                            print(f"⚠️ Search button also failed: {ticker_url}")
                            if attempt < max_retries - 1:
                                continue
                            else:
                                return False
                    except Exception as click_error:
                        print(f"⚠️ Could not click search button: {click_error}")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            return False
                
                # Validate we have a ticker page
                if "/ticker/" not in ticker_url:
                    print(f"⚠️ Search did not lead to ticker page for {ticker}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return False
                
                # Scrape scores
                scores = self._scrape_scores(ticker)
                if not scores:
                    print(f"⚠️ Failed to scrape scores for {ticker} on attempt {attempt+1}")
                    if attempt < max_retries - 1:
                        time.sleep(4)  # Wait before retrying
                        continue
                    else:
                        return False
                
                # Get ticker details using base URL
                ticker_data = self._get_calculator_data(ticker, base_ticker_url)
                if not ticker_data:
                    print(f"⚠️ Failed to get ticker data for {ticker} on attempt {attempt+1}")
                    if attempt < max_retries - 1:
                        time.sleep(4)  # Wait before retrying
                        continue
                    else:
                        return False
                
                # Combine data
                data = {**scores, **ticker_data}
                
                # Clean all data by removing commas and decimal parts
                for key, value in data.items():
                    if isinstance(value, str) and value != 'N/A':
                        # Remove commas and convert decimals to integers
                        import re
                        cleaned = value.replace(',', '')
                        # Extract integer part from decimal numbers
                        match = re.search(r'(\d+)(?:\.\d+)?', cleaned)
                        if match:
                            data[key] = cleaned.replace(match.group(0), match.group(1))
                        else:
                            data[key] = cleaned
                
                # Save data to CSV
                self._save_to_csv(ticker, data)
                
                return True
                
            except Exception as e:
                print(f"⚠️ Failed to process {ticker} on attempt {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(4)  # Wait before retrying
                else:
                    return False
        
        return False
    
    def _scrape_scores(self, ticker):
        """Scrape Rule1, Management, and Moat scores"""
        try:
            # Wait for the container and its content to be fully loaded
            try:
                # Wait for the container to be present with scores loaded
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "rule-one-number")]'))
                )
                # Brief wait for content to populate
                WebDriverWait(self.driver, 3).until(
                    lambda driver: len(driver.find_elements(By.XPATH, '//div[contains(@class, "rule-one-number")]//span[contains(@class, "full-header") or contains(@class, "number-box")]')) > 0
                )
                print(f"✅ Found rule-one-number container with content for {ticker}")
            except (TimeoutException, NoSuchElementException):
                print(f"⚠️ Could not find rule-one-number container for {ticker}")
                
                # Try to reload the page and search again
                try:
                    print("🔄 Attempting to reload page and search again...")
                    current_url = self.driver.current_url
                    
                    # Check if we're on a ticker page
                    if f"/ticker/" in current_url:
                        # Extract the ticker symbol from the URL
                        parts = current_url.split("/ticker/")
                        if len(parts) > 1:
                            ticker_part = parts[1].split("/")[0]
                            # Reload the page
                            self.driver.get(f"https://ruleonetoolbox.com/ticker/{ticker_part}")
                            # Wait for rule-one-number container to load
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "rule-one-number")]'))
                            )
                            
                            # Try to find the container again
                            try:
                                container = WebDriverWait(self.driver, 15).until(
                                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "rule-one-number")]'))
                                )
                                print(f"✅ Found rule-one-number container after reload for {ticker}")
                            except (TimeoutException, NoSuchElementException):
                                print(f"⚠️ Still could not find rule-one-number container after reload for {ticker}")
                                container = None
                except Exception as reload_error:
                    print(f"⚠️ Error during page reload: {reload_error}")
                    container = None
            
            # Extract all scores immediately without waiting
            rule1_selectors = [
                '//div[contains(@class, "rule-one-number")]//span[contains(@class, "full-header")]',
                '//div[contains(@class, "rule-one-number")]//span[contains(@class, "compact-header")]/span[1]',
                '//span[contains(@class, "full-header") and contains(@class, "text-lg")]',
                '//span[contains(@class, "rounded-sm") and contains(@class, "py-2") and contains(@class, "px-4")]'
            ]
            
            moat_selectors = [
                '//div[contains(@class, "rule-one-number")]//div[contains(@class, "flex-col")][1]//span[contains(@class, "number-box")]',
                '//div[contains(@class, "rule-one-number")]//span[text()="Moat"]/preceding-sibling::span',
                '//span[contains(@class, "number-box") and contains(@class, "text-lg")][1]',
                '//div[contains(text(), "Moat")]/preceding-sibling::span[contains(@class, "text-lg")]'
            ]
            
            management_selectors = [
                '//div[contains(@class, "rule-one-number")]//div[contains(@class, "flex-col")][2]//span[contains(@class, "number-box")]',
                '//div[contains(@class, "rule-one-number")]//span[text()="Management"]/preceding-sibling::span',
                '//div[contains(@class, "rule-one-number")]//span[text()="Mgmt"]/preceding-sibling::span',
                '//span[contains(@class, "number-box") and contains(@class, "text-lg")][2]',
                '//div[contains(text(), "Management")]/preceding-sibling::span[contains(@class, "text-lg")]'
            ]
            
            # Extract scores immediately
            rule1_score = None
            for selector in rule1_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    rule1_score = element.text.strip()
                    if rule1_score:
                        break
                except NoSuchElementException:
                    continue
            
            moat_score = None
            for selector in moat_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    moat_score = element.text.strip()
                    if moat_score:
                        break
                except NoSuchElementException:
                    continue
            
            management_score = None
            for selector in management_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    management_score = element.text.strip()
                    if management_score:
                        break
                except NoSuchElementException:
                    continue
            
            # If immediate extraction failed, try with brief wait as fallback
            if not rule1_score or not moat_score or not management_score:
                print(f"⚠️ Immediate extraction failed, trying with brief wait for {ticker}")
                
                # Try Rule1 score with wait if not found
                if not rule1_score:
                    for selector in rule1_selectors:
                        try:
                            element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            rule1_score = element.text.strip()
                            if rule1_score:
                                break
                        except (TimeoutException, NoSuchElementException):
                            continue
                
                # Try Moat score with wait if not found
                if not moat_score:
                    for selector in moat_selectors:
                        try:
                            element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            moat_score = element.text.strip()
                            if moat_score:
                                break
                        except (TimeoutException, NoSuchElementException):
                            continue
                
                # Try Management score with wait if not found
                if not management_score:
                    for selector in management_selectors:
                        try:
                            element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            management_score = element.text.strip()
                            if management_score:
                                break
                        except (TimeoutException, NoSuchElementException):
                            continue
                
                if not rule1_score or not moat_score or not management_score:
                    raise NoSuchElementException("Could not find one or more score elements")
            
            # Scrape company full name
            full_name = None
            name_selectors = [
                '//h1[contains(@class, "ticker-details__name")]',
                '//h1[@class="ticker-details__name"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.XPATH, selector)
                    full_name = name_element.text.strip()
                    if full_name:
                        break
                except NoSuchElementException:
                    continue
            
            if not full_name:
                full_name = "N/A"
            
            print(f"✅ Scraped scores for {ticker}: Rule1={rule1_score.replace(',', '') if rule1_score else 'N/A'}, Management={management_score.replace(',', '') if management_score else 'N/A'}, Moat={moat_score.replace(',', '') if moat_score else 'N/A'}, Name={full_name}")
            
            return {
                'rule1_score': rule1_score.replace(',', '') if rule1_score else 'N/A',
                'management_score': management_score.replace(',', '') if management_score else 'N/A',
                'moat_score': moat_score.replace(',', '') if moat_score else 'N/A',
                'full_name': full_name
            }
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"⚠️ Failed to scrape scores: {e}")
            
            # Last resort: try to get scores directly from the page source
            try:
                # Get the page source and look for the scores in the HTML
                page_source = self.driver.page_source
                
                # Try to extract scores using simple string parsing as a fallback
                if "rule-one-number" in page_source:
                    print("Attempting to extract scores from page source as fallback...")
                    
                    # Look for patterns in the HTML that might contain the scores
                    import re
                    
                    # Try to find Rule1 score
                    rule1_pattern = re.search(r'full-header[^>]*>\s*(\d+)\s*<', page_source)
                    rule1_score = rule1_pattern.group(1) if rule1_pattern else None
                    
                    # Try to find Moat score
                    moat_pattern = re.search(r'bg-yellow[^>]*>\s*(\d+)\s*<', page_source)
                    moat_score = moat_pattern.group(1) if moat_pattern else None
                    
                    # Try to find Management score
                    mgmt_pattern = re.search(r'bg-red-500[^>]*>\s*(\d+)\s*<', page_source)
                    management_score = mgmt_pattern.group(1) if mgmt_pattern else None
                    
                    if rule1_score and moat_score and management_score:
                        print(f"✅ Extracted scores from page source: Rule1={rule1_score.replace(',', '') if rule1_score else 'N/A'}, Management={management_score.replace(',', '') if management_score else 'N/A'}, Moat={moat_score.replace(',', '') if moat_score else 'N/A'}")
                        return {
                            'rule1_score': rule1_score,
                            'management_score': management_score,
                            'moat_score': moat_score
                        }
            except Exception as ex:
                print(f"⚠️ Failed to extract scores from page source: {ex}")
                
            return None
    
    def _get_calculator_data(self, ticker, base_ticker_url):
        """Scrape buy price and last price directly from ticker details page"""
        try:
            # No unnecessary wait - let WebDriverWait handle timing
            
            # Navigate to Growth Rate Analysis using base ticker URL
            growth_data = {'last_gr': 'N/A', 'long_gr': 'N/A'}
            if not self._navigate_to_growth_rate_analysis(base_ticker_url):
                print(f"⚠️ Failed to navigate to Growth Rate Analysis for {ticker}")
                # Continue anyway to try scraping without this step
            else:
                # Click Save Composite Growth Rate first
                if not self._save_composite_growth_rate():
                    print(f"⚠️ Failed to save composite growth rate for {ticker}")
                    # Continue anyway to try scraping without this step
                
                # Now scrape growth rate data after saving (when data is updated)
                growth_data = self._scrape_growth_rate_data()
            
            # Navigate to Valuation Calculators using base ticker URL
            if not self._navigate_to_valuation_calculators(base_ticker_url):
                print(f"⚠️ Failed to navigate to Valuation Calculators for {ticker}")
            
            # Select Composite GR and Calculate
            if not self._select_composite_gr_and_calculate():
                print(f"⚠️ Failed to select Composite GR and calculate for {ticker}")
                # Continue anyway to try scraping without this step
            
            # Save Valuations before scraping buy price
            if not self._save_valuations():
                print(f"⚠️ Failed to save valuations for {ticker}")
                # Continue anyway to try scraping without this step
            

            
            # Scrape Buy Price from ticker details
            buy_price = None
            buy_price_selectors = [
                '//div[contains(@class, "ticker-details__meta") and contains(@class, "bs-callout-primary")][.//div[contains(@class, "ticker-details__label") and contains(text(), "Buy Price")]]/div/div[contains(@class, "ticker-details__value")]',
                '//div[contains(@class, "ticker-details__label") and contains(text(), "Buy Price")]/preceding-sibling::div[contains(@class, "ticker-details__value")]'
            ]
            
            for selector in buy_price_selectors:
                try:
                    buy_price_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    buy_price = buy_price_element.text.strip()
                    if buy_price:
                        break
                except:
                    continue
            
            # Scrape PBT at Current Price
            pbt_current_price = None
            pbt_selectors = [
                '//div[contains(@class, "calculator-results__list-label") and contains(text(), "PBT at Current Price")]/following-sibling::div[contains(@class, "calculator-results__list-value")]',
                '//div[contains(text(), "PBT at Current Price")]/following-sibling::div'
            ]
            
            for selector in pbt_selectors:
                try:
                    pbt_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    pbt_current_price = pbt_element.text.strip()
                    if pbt_current_price:
                        break
                except:
                    continue
            

            
            if not buy_price:
                print(f"⚠️ Could not find Buy Price for {ticker}")
                buy_price = "N/A"
            

            
            print(f"✅ Scraped ticker details for {ticker}: Buy Price={buy_price.replace(',', '') if buy_price and buy_price != 'N/A' else buy_price}, PBT={pbt_current_price.replace(',', '') if pbt_current_price else 'N/A'}")
            
            # Remove commas from price fields
            if buy_price and buy_price != 'N/A':
                buy_price = buy_price.replace(',', '')
            if pbt_current_price:
                pbt_current_price = pbt_current_price.replace(',', '')
            
            return {
                'buy_price': buy_price,
                'guru': pbt_current_price if pbt_current_price else "N/A",
                **growth_data
            }
            
        except Exception as e:
            print(f"⚠️ Failed to get ticker details: {e}")
            return None
    
    def _save_to_csv(self, ticker, data):
        """Save ticker data to CSV file"""
        try:
            file_exists = os.path.isfile(self.csv_file)
            
            with open(self.csv_file, 'a', newline='') as csvfile:
                fieldnames = ['ticker', 'full_name', 'rule1_score', 'management_score', 'moat_score', 'buy_price', 'last_price', 'last_gr', 'long_gr', 'guru']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'ticker': ticker,
                    'full_name': data.get('full_name', 'N/A'),
                    'rule1_score': data.get('rule1_score', 'N/A'),
                    'management_score': data.get('management_score', 'N/A'),
                    'moat_score': data.get('moat_score', 'N/A'),
                    'buy_price': data.get('buy_price', 'N/A'),
                    'last_price': data.get('last_price', 'N/A'),
                    'last_gr': data.get('last_gr', 'N/A'),
                    'long_gr': data.get('long_gr', 'N/A'),
                    'guru': data.get('guru', 'N/A')
                })
                

            return True
            
        except Exception as e:
            print(f"⚠️ Failed to save data to CSV: {e}")
            return False
    
    def _navigate_to_ticker_page(self, ticker):
        """Navigate to individual ticker page by directly accessing the URL"""
        try:
            # Try different ticker formats (plain, NAS:, NYSE:)
            ticker_formats = [
                ticker,
                f"NAS:{ticker}",
                f"NYSE:{ticker}"
            ]
            
            for ticker_format in ticker_formats:
                try:
                    # Directly navigate to the ticker page
                    ticker_url = f"https://ruleonetoolbox.com/ticker/{ticker_format}"
                    self.driver.get(ticker_url)
                    print(f"✅ Directly navigated to ticker page: {ticker_url}")
                    
                    # Wait for ticker page elements to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "ticker-details")]'))
                    )
                    
                    # Check if we landed on a valid ticker page
                    if "/ticker/" in self.driver.current_url:
                        return True
                except:
                    continue
            
            print(f"⚠️ Could not navigate to ticker page for {ticker}")
            return False
        except Exception as e:
            print(f"❌ Failed to navigate to ticker page for {ticker}: {e}")
            return False
    
    def _navigate_to_growth_rate_analysis(self, base_ticker_url):
        """Navigate to Growth Rate Analysis page using the base ticker URL"""
        try:
            # Build growth rates URL from base
            growth_rates_url = f"{base_ticker_url}/analysis/growth-rates"
            
            self.driver.get(growth_rates_url)
            print(f"✅ Navigated to Growth Rate Analysis: {growth_rates_url}")
            
            # Wait for Save Composite Growth Rate button
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(@class, "p-button-label") and contains(text(), "Save Composite Growth Rate")]'))
            )
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to Growth Rate Analysis: {e}")
            return False
    
    def _scrape_growth_rate_data(self):
        """Scrape dividend and cash per share data before saving composite growth rate"""
        try:
            # No unnecessary wait - WebDriverWait will handle element detection
            
            # Extract growth rates immediately
            dividend_selectors = [
                '//div[contains(@class, "lastSavedComposite")]//span[contains(@class, "font-bold")]',
                '//span[contains(text(), "Last Saved Composite GR")]/following-sibling::span[contains(@class, "font-bold")]',
                '//div[contains(@class, "lastSavedComposite")]//span[contains(@class, "text-xl")]'
            ]
            
            cash_selectors = [
                '//div[contains(@class, "analyst")]//span[contains(@class, "font-bold")]',
                '//span[contains(text(), "Analyst Estimated Long-Term GR")]/following-sibling::span[contains(@class, "font-bold")]',
                '//div[contains(@class, "analyst")]//span[contains(@class, "text-xl")]'
            ]
            
            last_gr = "N/A"
            for selector in dividend_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    dividend_text = element.text.strip()
                    if dividend_text:
                        import re
                        last_gr = dividend_text.replace('%', '').replace(',', '')
                        match = re.search(r'(\d+)(?:\.\d+)?', last_gr)
                        last_gr = match.group(1) if match else last_gr
                        break
                except NoSuchElementException:
                    continue
            
            long_gr = "N/A"
            for selector in cash_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    cash_text = element.text.strip()
                    if cash_text:
                        import re
                        long_gr = cash_text.replace('%', '').replace(',', '')
                        match = re.search(r'(\d+)(?:\.\d+)?', long_gr)
                        long_gr = match.group(1) if match else long_gr
                        break
                except NoSuchElementException:
                    continue
            
            print(f"✅ Scraped growth rate data: Last GR={last_gr}, Long GR={long_gr}")
            return {
                'last_gr': last_gr,
                'long_gr': long_gr
            }
            
        except Exception as e:
            print(f"⚠️ Failed to scrape growth rate data: {e}")
            return {'last_gr': 'N/A', 'long_gr': 'N/A'}
    
    def _save_composite_growth_rate(self):
        """Click Save Composite Growth Rate button and handle toast notification"""
        try:
            save_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(@class, "p-button-label") and contains(text(), "Save Composite Growth Rate")]'))
            )
            save_button.click()
            print("✅ Clicked Save Composite Growth Rate")
            # Wait briefly for save action to complete
            WebDriverWait(self.driver, 2).until(
                lambda driver: True  # Just a brief wait
            )
            
            # Handle toast notification close button
            try:
                toast_close = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//span[contains(@class, "p-toast-icon-close-icon") and contains(@class, "pi-times")]'))
                )
                toast_close.click()
                print("✅ Closed toast notification")
                time.sleep(0.5)
            except TimeoutException:
                print("ℹ️ No toast notification found or already closed")
            
            return True
        except Exception as e:
            print(f"⚠️ Failed to save composite growth rate: {e}")
            return False
    
    def _navigate_to_valuation_calculators(self, base_ticker_url):
        """Navigate to Valuation Calculators page using the base ticker URL"""
        try:
            # Build calculators URL from base
            calculators_url = f"{base_ticker_url}/analysis/calculators"
            
            self.driver.get(calculators_url)
            print(f"✅ Navigated to Valuation Calculators: {calculators_url}")
            
            # Wait for Composite GR radio button
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//p-radiobutton[@label="Composite GR"]'))
            )
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to Valuation Calculators: {e}")
            return False
    
    def _select_composite_gr_and_calculate(self):
        """Select Composite GR radio button and click Calculate"""
        try:
            # Select Composite GR radio button
            composite_radio = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//p-radiobutton[@label="Composite GR"]//div[contains(@class, "p-radiobutton-box")]'))
            )
            composite_radio.click()
            print("✅ Selected Composite GR radio button")
            # Wait for radio button selection to register
            WebDriverWait(self.driver, 2).until(
                lambda driver: driver.find_element(By.XPATH, '//p-radiobutton[@label="Composite GR"]//div[contains(@class, "p-radiobutton-box")]').get_attribute('class').find('p-highlight') != -1
            )
            
            # Click Calculate button
            calculate_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//span[contains(@class, "p-button-label") and contains(text(), "Calculate")]]'))
            )
            calculate_button.click()
            print("✅ Clicked Calculate button")
            # Wait for calculation results to load
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "calculator-results")]'))
            )
            return True
        except Exception as e:
            print(f"⚠️ Failed to select Composite GR and calculate: {e}")
            return False
    
    def _save_valuations(self):
        """Click Save Valuations button"""
        try:
            save_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(@class, "p-button-label") and contains(text(), "Save Valuations")]'))
            )
            save_button.click()
            print("✅ Clicked Save Valuations")
            # Wait for save action to complete
            WebDriverWait(self.driver, 3).until(
                lambda driver: True  # Brief wait for save
            )
            return True
        except Exception as e:
            print(f"⚠️ Failed to save valuations: {e}")
            return False
    
    def _navigate_back_to_search(self):
        """Navigate back to the search page using direct URL"""
        try:
            # Directly navigate to the stocks search page
            self.driver.get("https://ruleonetoolbox.com/explore/stocks")
            print("✅ Directly navigated to Stock Scan page")
            time.sleep(4)
            return True
        except Exception as e:
            print(f"❌ Error navigating to search page: {e}")
            return False
    

    
    def close(self):
        """Clean up resources"""
        # Note: We don't automatically close the driver here if it was passed in
        # This allows the main script to control when to close the browser

if __name__ == "__main__":
    searcher = TickerSearcher()
    try:
        searcher.combine_and_search_tickers()
    finally:
        searcher.close()