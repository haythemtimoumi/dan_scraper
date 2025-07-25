#!/usr/bin/env python
# Guru Portfolio Scraper

import time
import csv
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.source_tracker import save_ticker_source
from core.auth_rule1 import Rule1Auth
from core.browser import get_driver

class GuruScraper:
    """Scraper for Rule1Toolbox Guru Portfolio data"""
    
    def __init__(self, driver=None):
        """
        Initialize the GuruScraper.
        
        Args:
            driver: Existing Selenium WebDriver instance (optional)
        """
        self.driver = driver if driver else get_driver()
        self.guru_url = "https://ruleonetoolbox.com/explore/guru-portfolio"
        self.guru_data = []
        self.guru_tickers = set()  # Use a set to avoid duplicates
        self.auth = Rule1Auth(self.driver)  # Initialize auth helper
        self._driver_created = driver is None  # Track if we created the driver
        
    def navigate_to_guru_page(self):
        """Navigate to the Guru Portfolio page"""
        try:
            print("🔍 Navigating to Guru Portfolio page...")
            self.driver.get(self.guru_url)
            
            # Wait for the page to load (guru table to appear)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            
            # Wait for the table to be fully loaded
            print("⏳ Waiting for guru list to fully load...")
            time.sleep(5)
            
            print("✅ Successfully navigated to Guru Portfolio page")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to Guru Portfolio page: {e}")
            return False
    
    def scrape_guru_list(self):
        """Scrape the list of gurus and their portfolio data"""
        print("🔍 Scraping guru list...")
        
        try:
            # Wait for the table to fully load
            time.sleep(5)
            
            # Get all guru links first (to avoid stale element issues)
            guru_links = []
            guru_names = []
            guru_ids = []
            
            # Find all guru links in the table
            links = self.driver.find_elements(By.CSS_SELECTOR, "td.font-semibold a")
            
            # Filter and collect valid guru links
            for link in links:
                try:
                    name = link.text.strip()
                    href = link.get_attribute("href")
                    
                    # Check if this is a valid guru entry
                    if "guruId=" in href:
                        guru_id = href.split("guruId=")[1]
                        guru_links.append(href)
                        guru_names.append(name)
                        guru_ids.append(guru_id)
                except Exception:
                    continue
            
            print(f"📊 Found {len(guru_links)} valid gurus")
            
            # Now process each guru one by one
            for i, (guru_href, guru_name, guru_id) in enumerate(zip(guru_links, guru_names, guru_ids)):
                try:
                    print(f"🔍 Processing guru {i+1}/{len(guru_links)}: {guru_name} (ID: {guru_id})")
                    
                    # Navigate directly to the guru's portfolio using the href
                    self.driver.get(guru_href)
                    
                    # Wait for the portfolio page to load
                    try:
                        WebDriverWait(self.driver, 30).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
                        )
                        time.sleep(3)
                        
                        # First try direct extraction from table
                        direct_tickers = []
                        try:
                            # Get all rows in the table
                            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                            print(f"Found {len(rows)} rows in {guru_name}'s portfolio table")
                            
                            # Try different selectors for ticker cells
                            for row in rows:
                                try:
                                    # Try first cell
                                    ticker_cell = row.find_element(By.CSS_SELECTOR, "td:first-child")
                                    ticker = ticker_cell.text.strip()
                                    
                                    # Skip non-ticker elements
                                    if ticker and len(ticker) <= 5 and ticker not in ['% of Portfolio', 'Ticker', 'Symbol'] and '%' not in ticker:
                                        direct_tickers.append(ticker)
                                        print(f"Found ticker directly from table: {ticker}")
                                except:
                                    # Try links in the row
                                    try:
                                        links = row.find_elements(By.TAG_NAME, "a")
                                        for link in links:
                                            href = link.get_attribute("href")
                                            if href and "/ticker/" in href:
                                                ticker = link.text.strip()
                                                if ticker and len(ticker) <= 5:
                                                    direct_tickers.append(ticker)
                                                    print(f"Found ticker from link: {ticker}")
                                    except:
                                        pass
                            
                            if direct_tickers:
                                print(f"✅ Found {len(direct_tickers)} tickers directly from table")
                        except Exception as table_error:
                            print(f"⚠️ Error extracting tickers directly from table: {table_error}")
                    except Exception as e:
                        print(f"⚠️ Error waiting for {guru_name}'s portfolio page to load: {e}")
                        continue
                    
                    # Extract tickers using fallback method (most reliable)
                    page_source = self.driver.page_source
                    
                    # Look for ticker patterns in the HTML - try multiple patterns
                    # First try standard pattern
                    ticker_pattern1 = re.compile(r'href="/ticker/([A-Z]+)"')
                    # Also try pattern with exchange prefix (NYSE:, NAS:)
                    ticker_pattern2 = re.compile(r'href="/ticker/(?:NYSE:|NAS:)?([A-Z\.]+)"')
                    # Try pattern for td elements that might contain tickers
                    ticker_pattern3 = re.compile(r'<td[^>]*>\s*([A-Z]{1,5})\s*</td>')
                    # Target the specific company-symbol pattern from the HTML
                    ticker_pattern4 = re.compile(r'class="compay-symbol[^>]*><span>([A-Z\.]+)</span>')
                    
                    # Also extract performance and last action data with more specific patterns
                    performance_pattern = re.compile(r'<td class="isNumberColumn is-highlight"[^>]*><span[^>]*>\s*([\d\.]+%)\s*</span>')
                    action_pattern = re.compile(r'<span class="pl-6">([^<]+)</span>')
                    
                    # Try to extract ticker-performance-action triplets
                    # This pattern looks for rows with ticker, performance, and action
                    row_pattern = re.compile(r'<tr[^>]*>.*?compay-symbol[^>]*><span>([A-Z\.]+)</span>.*?isNumberColumn is-highlight.*?<span[^>]*>\s*([\d\.]+%)\s*</span>.*?<span class="pl-6">([^<]+)</span>.*?</tr>', re.DOTALL)
                    
                    # Extract triplets (ticker, performance, action)
                    triplets = row_pattern.findall(page_source)
                    
                    # Create a dictionary to store performance and action by ticker
                    ticker_details = {}
                    for ticker, perf, action in triplets:
                        ticker_details[ticker] = {'performance': perf, 'action': action}
                    
                    # Also extract individual components as fallback
                    matches1 = ticker_pattern1.findall(page_source)
                    matches2 = ticker_pattern2.findall(page_source)
                    matches3 = ticker_pattern3.findall(page_source)
                    matches4 = ticker_pattern4.findall(page_source)
                    
                    # Extract performance and action data as fallback
                    performances = performance_pattern.findall(page_source)
                    actions = action_pattern.findall(page_source)
                    
                    # Combine all matches and remove duplicates
                    all_matches = set(matches1 + matches2 + matches3 + matches4)
                    regex_matches = [m for m in all_matches if len(m) <= 5 and m not in ['ABOUT', 'INDEX', 'TABLE']]
                    
                    # Combine direct tickers and regex matches
                    all_tickers = set(direct_tickers + regex_matches)
                    
                    if all_tickers:
                        print(f"✅ Found {len(all_tickers)} tickers in {guru_name}'s portfolio")
                        for ticker in all_tickers:
                            if ticker and len(ticker) <= 5 and ticker not in ['ABOUT', 'INDEX']:
                                # Get performance and action data if available
                                performance = "N/A"
                                last_action = "Unknown"
                                
                                # Check if we have details for this ticker
                                if ticker in ticker_details:
                                    performance = ticker_details[ticker]['performance']
                                    last_action = ticker_details[ticker]['action']
                                
                                # Add the data to the guru_data collection
                                self.guru_data.append({
                                    "guru_name": guru_name,
                                    "guru_id": guru_id,
                                    "ticker": ticker,
                                    "performance": performance,
                                    "last_action": last_action
                                })
                                
                                # Add the ticker to the guru_tickers set
                                self.guru_tickers.add(ticker)
                                
                                # Mark the ticker with 'guru_list' source
                                save_ticker_source(ticker, 'guru_list')
                                
                                print(f"Processed {ticker} from {guru_name}'s portfolio: Performance={performance}, Action={last_action}")
                    else:
                        # Last resort: try to find any stock symbols in the page
                        print(f"⚠️ No tickers found with standard methods, trying last resort for {guru_name}")
                        
                        # Look for common stock symbol patterns
                        last_resort_patterns = [
                            # General pattern for tickers
                            re.compile(r'>[\s\n]*([A-Z]{1,5})[\s\n]*<'),
                            # Specific pattern for company-symbol class
                            re.compile(r'class="compay-symbol[^>]*>\s*<span>\s*([A-Z\.]{1,5})\s*</span>'),
                            # Pattern for td with ticker
                            re.compile(r'<td[^>]*>\s*<span[^>]*>\s*([A-Z\.]{1,5})\s*</span>\s*</td>')
                        ]
                        
                        last_resort_matches = []
                        for pattern in last_resort_patterns:
                            matches = pattern.findall(page_source)
                            last_resort_matches.extend(matches)
                        
                        # Filter out common HTML tags and non-ticker text
                        common_tags = ['HTML', 'HEAD', 'BODY', 'DIV', 'SPAN', 'TABLE', 'TBODY', 'THEAD', 'TR', 'TD', 'TH', 'UL', 'LI', 'NAV', 'MAIN', 'FORM', 'INPUT', 'HELD', 'SOLD', 'ADDED', 'NEW']
                        common_words = ['THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'WHAT', 'WHEN', 'WHERE', 'WHY', 'HOW', 'WHO', 'WHICH']
                        filtered_matches = []
                        
                        for m in last_resort_matches:
                            # Only include if it looks like a ticker (1-5 chars, all caps)
                            if (len(m) >= 1 and len(m) <= 5 and 
                                m not in common_tags and 
                                m not in common_words and
                                m.isupper() and
                                not m.isdigit()):
                                filtered_matches.append(m)
                        
                        if filtered_matches:
                            print(f"✅ Found {len(filtered_matches)} potential tickers with last resort method")
                            for ticker in set(filtered_matches):
                                # Get performance and action data if available
                                performance = "N/A"
                                last_action = "Unknown"
                                
                                # Check if we have details for this ticker
                                if ticker in ticker_details:
                                    performance = ticker_details[ticker]['performance']
                                    last_action = ticker_details[ticker]['action']
                                
                                # Add the data to the guru_data collection
                                self.guru_data.append({
                                    "guru_name": guru_name,
                                    "guru_id": guru_id,
                                    "ticker": ticker,
                                    "performance": performance,
                                    "last_action": last_action
                                })
                                
                                # Add the ticker to the guru_tickers set
                                self.guru_tickers.add(ticker)
                                
                                # Mark the ticker with 'guru_list' source
                                save_ticker_source(ticker, 'guru_list')
                                
                                print(f"Processed {ticker} from {guru_name}'s portfolio (last resort): Performance={performance}, Action={last_action}")
                        else:
                            print(f"⚠️ No tickers found in {guru_name}'s portfolio with any method")
                    
                except Exception as e:
                    print(f"⚠️ Error processing guru {guru_name}: {e}")
                    # Continue to the next guru
            
            print(f"✅ Successfully scraped data for {len(self.guru_data)} guru-ticker combinations")
            print(f"✅ Found {len(self.guru_tickers)} unique tickers from guru portfolios")
            
            return True
        
        except Exception as e:
            print(f"❌ Error scraping guru list: {e}")
            return False
    
    def save_guru_data(self):
        """Save the guru data to a CSV file"""
        if not self.guru_data:
            print("⚠️ No guru data to save")
            return False
        
        try:
            # Save to project root directory to ensure consistency
            filename = "guru_data.csv"
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ["guru_name", "guru_id", "ticker", "performance", "last_action"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for data in self.guru_data:
                    writer.writerow(data)
            
            print(f"✅ Guru data saved to {filename}")
            return True
        
        except Exception as e:
            print(f"❌ Error saving guru data: {e}")
            return False
    
    def save_guru_tickers(self):
        """Save the guru tickers to a text file"""
        if not self.guru_tickers:
            print("⚠️ No guru tickers to save")
            return False
        
        try:
            # Save to project root directory to ensure it's found by the ticker searcher
            filename = "guru_tickers.txt"
            with open(filename, 'w') as f:
                for ticker in sorted(self.guru_tickers):
                    f.write(f"{ticker}\n")
            
            print(f"✅ Guru tickers saved to {filename}")
            return True
        
        except Exception as e:
            print(f"❌ Error saving guru tickers: {e}")
            return False
    
    def add_fallback_tickers(self):
        """Add a fallback list of common guru tickers if no tickers were found"""
        if not self.guru_tickers:
            print("⚠️ No guru tickers found with scraping, adding fallback list")
            # Common tickers often held by gurus
            fallback_tickers = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "META", "BRK.B", "BRK.A", "JPM", "JNJ", "V", 
                "PG", "MA", "UNH", "HD", "BAC", "NVDA", "PYPL", "DIS", "ADBE", "CRM", 
                "NFLX", "INTC", "VZ", "CSCO", "ABT", "KO", "PEP", "NKE", "MRK", "WMT"
            ]
            
            for ticker in fallback_tickers:
                self.guru_tickers.add(ticker)
                save_ticker_source(ticker, 'guru_fallback')
                
                # Also add to guru_data
                self.guru_data.append({
                    "guru_name": "Fallback",
                    "guru_id": "0",
                    "ticker": ticker,
                    "performance": "N/A",
                    "last_action": "Fallback"
                })
                
            print(f"✅ Added {len(fallback_tickers)} fallback tickers")
            return True
        return False
    
    def run(self):
        """Run the complete guru scraping process"""
        # Process all gurus
        if self.navigate_to_guru_page():
            if self.scrape_guru_list():
                # If no tickers were found, add fallback list
                if not self.guru_tickers:
                    self.add_fallback_tickers()
                    
                self.save_guru_data()
                self.save_guru_tickers()
                return True
        return False
    
    def close(self):
        """Close the browser driver if we created it"""
        if self._driver_created and self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"⚠️ Error closing driver: {e}")