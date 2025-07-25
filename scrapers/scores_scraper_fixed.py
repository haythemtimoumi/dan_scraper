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
        self.driver = driver if driver else get_driver()
        self.wait = WebDriverWait(self.driver, 10)
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
        # First check if we're already logged in by looking for dashboard elements
        try:
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
                "scraped_tickers.txt",
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
        Combine tickers from multiple files into one
        Returns count of unique tickers found
        """
        unique_tickers = set()
        
        for file_path in input_files:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        ticker = line.strip()
                        if ticker:
                            unique_tickers.add(ticker)
                print(f"✅ Read {len(unique_tickers)} tickers from {file_path}")
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
        
        success_count = 0
        for ticker in tickers:
            if self._process_single_ticker(ticker):
                success_count += 1
        
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
        for attempt in range(max_retries):
            try:
                print(f"\n🔍 Processing {ticker} (attempt {attempt+1}/{max_retries})...")
                
                # Find and clear search input
                search_input = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        '//span[contains(@class, "p-input-icon-left")]//input[contains(@placeholder, "Search for Stocks")]'
                    ))
                )
                search_input.clear()
                
                # Enter and submit ticker
                search_input.send_keys(ticker)
                search_input.send_keys(Keys.ENTER)
                print(f"✅ Search submitted for {ticker}")
                
                # Wait for results (adjust timing as needed)
                time.sleep(3)
                
                # Scrape scores
                scores = self._scrape_scores(ticker)
                if not scores:
                    print(f"⚠️ Failed to scrape scores for {ticker} on attempt {attempt+1}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retrying
                        continue
                    else:
                        return False
                
                # Click calculator icon to get sticker price
                calculator_data = self._get_calculator_data(ticker)
                if not calculator_data:
                    print(f"⚠️ Failed to get calculator data for {ticker} on attempt {attempt+1}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retrying
                        continue
                    else:
                        return False
                
                # Combine data and calculate percentage upside
                data = {**scores, **calculator_data}
                
                # Calculate percentage upside
                if 'sticker_price' in data and 'last_price' in data:
                    try:
                        sticker_price = float(data['sticker_price'].replace('$', '').replace(',', '').strip())
                        last_price = float(data['last_price'].replace('$', '').replace(',', '').strip())
                        percentage_upside = ((sticker_price - last_price) / last_price) * 100
                        data['percentage_upside'] = f"{percentage_upside:.2f}%"
                    except (ValueError, ZeroDivisionError) as e:
                        print(f"⚠️ Error calculating percentage upside: {e}")
                        data['percentage_upside'] = "N/A"
                
                # Save data to CSV
                self._save_to_csv(ticker, data)
                
                return True
                
            except Exception as e:
                print(f"⚠️ Failed to process {ticker} on attempt {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retrying
                else:
                    return False
        
        return False
    
    def _scrape_scores(self, ticker):
        """Scrape Rule1, Management, and Moat scores"""
        try:
            # Wait for scores to be visible
            time.sleep(3)  # Increased wait time
            
            # Find the rule-one-number div container first
            try:
                # Wait for the container to be present
                container = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "rule-one-number")]'))
                )
                print(f"✅ Found rule-one-number container for {ticker}")
            except (TimeoutException, NoSuchElementException):
                print(f"⚠️ Could not find rule-one-number container for {ticker}")
                # Try to proceed anyway with direct selectors
                container = None
            
            # Try multiple XPath patterns for Rule1 Score
            rule1_score = None
            rule1_selectors = [
                # New selectors based on the HTML
                '//div[contains(@class, "rule-one-number")]//span[contains(@class, "full-header")]',
                '//div[contains(@class, "rule-one-number")]//span[contains(@class, "compact-header")]/span[1]',
                # Original selectors as fallback
                '//span[contains(@class, "full-header") and contains(@class, "text-lg")]',
                '//span[contains(@class, "rounded-sm") and contains(@class, "py-2") and contains(@class, "px-4")]'
            ]
            
            for selector in rule1_selectors:
                try:
                    rule1_score = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    ).text.strip()
                    if rule1_score:
                        break
                except:
                    continue
            
            if not rule1_score:
                raise NoSuchElementException("Could not find Rule1 Score element")
            
            # Try multiple XPath patterns for Moat Score
            moat_score = None
            moat_selectors = [
                # New selectors based on the HTML
                '//div[contains(@class, "rule-one-number")]//div[contains(@class, "flex-col")][1]//span[contains(@class, "number-box")]',
                '//div[contains(@class, "rule-one-number")]//span[text()="Moat"]/preceding-sibling::span',
                # Original selectors as fallback
                '//span[contains(@class, "number-box") and contains(@class, "text-lg")][1]',
                '//div[contains(text(), "Moat")]/preceding-sibling::span[contains(@class, "text-lg")]'
            ]
            
            for selector in moat_selectors:
                try:
                    moat_score = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    ).text.strip()
                    if moat_score:
                        break
                except:
                    continue
            
            if not moat_score:
                raise NoSuchElementException("Could not find Moat Score element")
            
            # Try multiple XPath patterns for Management Score
            management_score = None
            management_selectors = [
                # New selectors based on the HTML
                '//div[contains(@class, "rule-one-number")]//div[contains(@class, "flex-col")][2]//span[contains(@class, "number-box")]',
                '//div[contains(@class, "rule-one-number")]//span[text()="Management"]/preceding-sibling::span',
                '//div[contains(@class, "rule-one-number")]//span[text()="Mgmt"]/preceding-sibling::span',
                # Original selectors as fallback
                '//span[contains(@class, "number-box") and contains(@class, "text-lg")][2]',
                '//div[contains(text(), "Management")]/preceding-sibling::span[contains(@class, "text-lg")]'
            ]
            
            for selector in management_selectors:
                try:
                    management_score = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    ).text.strip()
                    if management_score:
                        break
                except:
                    continue
            
            if not management_score:
                raise NoSuchElementException("Could not find Management Score element")
            
            print(f"✅ Scraped scores for {ticker}: Rule1={rule1_score}, Management={management_score}, Moat={moat_score}")
            
            return {
                'rule1_score': rule1_score,
                'management_score': management_score,
                'moat_score': moat_score
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
                        print(f"✅ Extracted scores from page source: Rule1={rule1_score}, Management={management_score}, Moat={moat_score}")
                        return {
                            'rule1_score': rule1_score,
                            'management_score': management_score,
                            'moat_score': moat_score
                        }
            except Exception as ex:
                print(f"⚠️ Failed to extract scores from page source: {ex}")
                
            return None
    
    def _get_calculator_data(self, ticker):
        """Click calculator icon and scrape sticker price and last price"""
        try:
            # Try multiple selectors for calculator icon
            calculator_icon = None
            calculator_selectors = [
                '//a[contains(@class, "ticker-details__calculatorIcon")]',
                '//a[contains(@href, "/ticker/") and contains(@href, "/analysis/calculators")]',
                '//img[contains(@src, "calc.svg")]/parent::a',
                '//a[contains(@href, "calculators")]'
            ]
            
            for selector in calculator_selectors:
                try:
                    calculator_icon = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if calculator_icon:
                        break
                except:
                    continue
            
            if not calculator_icon:
                raise NoSuchElementException("Could not find calculator icon")
            
            # FIXED: Handle toast messages and use JavaScript click to avoid ElementClickInterceptedException
            try:
                # First try to dismiss any toast messages that might be intercepting clicks
                try:
                    toast_messages = self.driver.find_elements(By.XPATH, '//div[contains(@class, "p-toast-message")]')
                    if toast_messages:
                        for toast in toast_messages:
                            self.driver.execute_script("arguments[0].style.display='none';", toast)
                            print(f"✅ Dismissed toast message that might intercept clicks")
                except Exception as toast_error:
                    print(f"⚠️ Error handling toast messages: {toast_error}")
                
                # Use JavaScript to click the calculator icon
                self.driver.execute_script("arguments[0].click();", calculator_icon)
                print(f"✅ Clicked calculator icon for {ticker} using JavaScript")
            except Exception as js_error:
                print(f"⚠️ JavaScript click failed: {js_error}. Trying regular click...")
                try:
                    calculator_icon.click()
                    print(f"✅ Clicked calculator icon for {ticker} using regular click")
                except ElementClickInterceptedException:
                    # If regular click is intercepted, try one more approach
                    print(f"⚠️ Regular click was intercepted. Trying to navigate directly to calculator URL...")
                    try:
                        # Try to extract the calculator URL from the href attribute
                        calculator_url = calculator_icon.get_attribute("href")
                        if calculator_url:
                            self.driver.get(calculator_url)
                            print(f"✅ Navigated directly to calculator URL for {ticker}")
                        else:
                            raise ValueError("Could not get calculator URL from href attribute")
                    except Exception as url_error:
                        print(f"❌ Failed to navigate directly to calculator URL: {url_error}")
                        raise
            
            # Wait for calculator page to load
            time.sleep(5)  # Increased wait time
            
            # Try multiple selectors for Sticker Price
            sticker_price = None
            sticker_selectors = [
                '//div[contains(@class, "calculator-results__value-numbers")]',
                '//div[contains(text(), "Sticker Price")]/following-sibling::div[contains(@class, "value")]',
                '//span[contains(@class, "calculator-results__currency-symbol")]/parent::div'
            ]
            
            for selector in sticker_selectors:
                try:
                    sticker_price = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    ).text.strip()
                    if sticker_price:
                        break
                except:
                    continue
            
            if not sticker_price:
                raise NoSuchElementException("Could not find Sticker Price element")
            
            # Try multiple selectors for Last Price
            last_price = None
            last_price_selectors = [
                '//div[contains(@class, "calculator-results__value-lastnumbers")]',
                '//div[contains(text(), "Last Price")]/following-sibling::div[contains(@class, "value")]',
                '//span[contains(@class, "calculator-results__currency-symbol-lastPrice")]/parent::div'
            ]
            
            for selector in last_price_selectors:
                try:
                    last_price = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    ).text.strip()
                    if last_price:
                        break
                except:
                    continue
            
            if not last_price:
                raise NoSuchElementException("Could not find Last Price element")
                
            # Navigate back to search page
            self._navigate_back_to_search()
            
            print(f"✅ Scraped calculator data for {ticker}: Sticker Price={sticker_price}, Last Price={last_price}")
            
            return {
                'sticker_price': sticker_price,
                'last_price': last_price
            }
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"⚠️ Failed to get calculator data: {e}")
            return None
    
    def _save_to_csv(self, ticker, data):
        """Save ticker data to CSV file"""
        try:
            file_exists = os.path.isfile(self.csv_file)
            
            with open(self.csv_file, 'a', newline='') as csvfile:
                fieldnames = ['ticker', 'rule1_score', 'management_score', 'moat_score', 'sticker_price', 'last_price', 'percentage_upside']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'ticker': ticker,
                    'rule1_score': data.get('rule1_score', 'N/A'),
                    'management_score': data.get('management_score', 'N/A'),
                    'moat_score': data.get('moat_score', 'N/A'),
                    'sticker_price': data.get('sticker_price', 'N/A'),
                    'last_price': data.get('last_price', 'N/A'),
                    'percentage_upside': data.get('percentage_upside', 'N/A')
                })
                
            print(f"✅ Saved data for {ticker} to ticker_data.csv")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to save data to CSV: {e}")
            return False
    
    def _navigate_back_to_search(self):
        """Navigate back to the search page"""
        try:
            # Try to find and click the "Explore" menu
            explore_selectors = [
                '//a[@id="primaryMenuItemExplore"]',
                '//a[contains(@href, "/explore")]',
                '//a[contains(text(), "Explore")]'
            ]
            
            for selector in explore_selectors:
                try:
                    explore_menu = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    explore_menu.click()
                    time.sleep(1)
                    break
                except:
                    continue
            
            # Try to find and click "Scan for Stocks"
            scan_selectors = [
                '//span[text()="Scan for Stocks"]',
                '//a[contains(@href, "/explore/stocks")]',
                '//a[contains(text(), "Scan for Stocks")]'
            ]
            
            for selector in scan_selectors:
                try:
                    scan_link = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    scan_link.click()
                    time.sleep(2)
                    return True
                except:
                    continue
            
            # If the above methods fail, try to use browser back button
            self.driver.back()
            time.sleep(2)
            
            # If we're still on calculator page, try to go back again
            if "calculators" in self.driver.current_url:
                self.driver.back()
                time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error navigating back to search page: {e}")
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