import os
import csv
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import the browser module from the core package
from core.browser import get_driver

class GoogleFinanceScraper:
    """
    Scraper for getting stock prices from Google Finance.
    """
    
    def __init__(self, driver=None, headless=True):
        """
        Initialize the Google Finance scraper.
        
        Args:
            driver: Optional existing webdriver instance
            headless: Whether to run in headless mode
        """
        self.driver = driver if driver else get_driver(headless=headless)
        self.base_url = "https://www.google.com/finance/quote/"
    
    def get_stock_price(self, ticker):
        """
        Get the current stock price for a ticker symbol.
        
        Args:
            ticker: The ticker symbol to look up
            
        Returns:
            float: The current stock price or None if not found
        """
        # Add market suffix if not present (default to NASDAQ)
        if ":" not in ticker:
            ticker = f"{ticker}:NASDAQ"
        
        url = f"{self.base_url}{ticker}"
        print(f"Getting price for {ticker} from {url}")
        
        try:
            self.driver.get(url)
            time.sleep(2)  # Wait for page to load
            
            # Try multiple selectors in order of preference
            selectors = [
                "div[data-last-price]",
                "div.YMlKec.fxKbKc",
                ".YMlKec.fxKbKc",
                ".P6K39c"
            ]
            
            price_text = None
            for selector in selectors:
                try:
                    # Wait for element to be present
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Try data attribute first
                    price_text = price_element.get_attribute("data-last-price")
                    
                    # If no data attribute, get text content
                    if not price_text:
                        price_text = price_element.text.strip()
                    
                    if price_text:
                        break
                        
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not price_text:
                print(f"No price found for {ticker}")
                return None
            
            # Clean the price text
            # Remove currency symbols, commas, and non-breaking spaces
            price_text = price_text.replace("$", "").replace(",", "").replace("\u00a0", "").strip()
            
            # Convert to float
            try:
                price = float(price_text)
                print(f"Found price for {ticker}: ${price}")
                return price
            except ValueError:
                print(f"Could not convert price text '{price_text}' to float for {ticker}")
                return None
                
        except Exception as e:
            print(f"Error getting price for {ticker}: {e}")
            return None
    
    def get_multiple_stock_prices(self, tickers_file, output_file="google_finance_prices.csv"):
        """
        Get stock prices for multiple tickers from a file.
        
        Args:
            tickers_file: Path to file containing ticker symbols (one per line)
            output_file: Path to save the results CSV
            
        Returns:
            dict: Dictionary mapping tickers to prices
        """
        results = {}
        
        # Read tickers from file
        try:
            with open(tickers_file, 'r') as f:
                tickers = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading tickers file: {e}")
            return results
        
        print(f"Getting prices for {len(tickers)} tickers...")
        
        # Get price for each ticker
        for ticker in tickers:
            price = self.get_stock_price(ticker)
            results[ticker] = price
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        # Save results to CSV
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ticker', 'last_price'])
                for ticker, price in results.items():
                    writer.writerow([ticker, price])
            print(f"Saved prices to {output_file}")
        except Exception as e:
            print(f"Error saving results to CSV: {e}")
        
        return results
    
    def close(self):
        """Close the browser if it exists."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                print(f"Error closing browser: {e}")


if __name__ == "__main__":
    # Example usage
    scraper = GoogleFinanceScraper()
    try:
        # Test with a single ticker
        price = scraper.get_stock_price("AAPL")
        print(f"AAPL price: ${price}")
        
        # Test with a file of tickers
        if os.path.exists("test_tickers.txt"):
            results = scraper.get_multiple_stock_prices("test_tickers.txt")
            print(f"Got prices for {len(results)} tickers")
    finally:
        scraper.close()