import csv
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from core.browser import get_driver

class StockScoresScraper:
    def __init__(self, driver=None, input_file="combined_tickers.txt", output_file="stockscores_data.csv"):
        """
        Initialize the StockScoresScraper.
        
        Args:
            driver: Optional Selenium WebDriver instance. If not provided, a new one will be created.
            input_file: Path to file containing tickers to scrape (default: combined_tickers.txt)
            output_file: Path to CSV file for saving data (default: stockscores_data.csv)
        """
        if driver:
            self.driver = driver
            self.should_close_driver = False
        else:
            # Use the browser module from your project in headless mode for VPS
            self.driver = get_driver(headless=True)
            self.should_close_driver = True
            
        self.driver.implicitly_wait(5)
        self.input_file = input_file
        self.output_file = output_file
        self.wait = WebDriverWait(self.driver, 10)

    def read_tickers(self):
        """Read tickers from the input file"""
        try:
            with open(self.input_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ Error reading ticker file: {e}")
            return []

    def scrape_scores(self, ticker, retries=3):
        """Scrape StockScores data for a single ticker"""
        attempt = 0
        while attempt <= retries:
            try:
                print(f"\n🌐 Scraping StockScores for: {ticker} (Attempt {attempt + 1})")
                # Navigate directly to the ticker URL
                self.driver.get(f"https://www.stockscores.com/charts/charts/?ticker={ticker}")
                
                # Wait dynamically for the chart to load
                try:
                    # Wait for chart image to appear
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="col_full"]/img'))
                    )
                except TimeoutException:
                    print(f"⚠️ Timeout waiting for chart to load for {ticker}")
                    # Continue anyway to try to get any available data

                try:
                    signal = self.driver.find_element(
                        By.XPATH, '//strong[contains(text(), "Signal")]/following::span[@style="font-size:24px;"]/b'
                    ).text.strip()
                except:
                    print(f"⚠️ Signal not found for {ticker}")
                    signal = "N/A"

                try:
                    sentiment = self.driver.find_element(
                        By.XPATH, '//strong[contains(text(), "Sentiment")]/following::span[@style="font-size:24px;"]/b'
                    ).text.strip()
                except:
                    print(f"⚠️ Sentiment not found for {ticker}")
                    sentiment = "N/A"

                try:
                    img_elem = self.driver.find_element(By.XPATH, '//div[@class="col_full"]/img')
                    chart_url = img_elem.get_attribute("src")
                    print(f"🔗 Chart URL for {ticker}: {chart_url}")
                except:
                    chart_url = "N/A"
                    print(f"⚠️ Chart URL not found for {ticker}")

                return signal, sentiment, chart_url

            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed for {ticker}: {e}")
                attempt += 1
                time.sleep(3)

        print(f"🚨 All attempts failed for {ticker}")
        return "N/A", "N/A", "N/A"

    def run(self):
        """Main method to run the scraper"""
        tickers = self.read_tickers()
        if not tickers:
            print("❌ No tickers found to process")
            return False
            
        print(f"🔍 Starting StockScores scraping for {len(tickers)} tickers...")
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if we need to create a new file or append to existing ticker_data.csv
        try:
            # First check if ticker_data.csv exists and has headers
            ticker_data_exists = False
            has_stockscores_columns = False
            try:
                with open("ticker_data.csv", 'r') as f:
                    ticker_data_exists = True
                    header = f.readline().strip().split(',')
                    has_stockscores_columns = all(col in header for col in ["Signal Score", "Sentiment Score", "Screenshot"])
            except FileNotFoundError:
                ticker_data_exists = False
                
            # Create stockscores_data.csv
            with open(self.output_file, "w", newline="", encoding="utf-8") as out_file:
                writer = csv.writer(out_file)
                writer.writerow(["Date", "Ticker", "Signal Score", "Sentiment Score", "Screenshot"])
                
                # Process tickers in batches to avoid long browser sessions
                batch_size = 20
                for i in range(0, len(tickers), batch_size):
                    batch = tickers[i:i+batch_size]
                    print(f"\n🔄 Processing batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1}")
                    
                    # Process each ticker in the batch
                    results = []
                    for ticker in batch:
                        signal, sentiment, chart_url = self.scrape_scores(ticker)
                        results.append([today, ticker, signal, sentiment, chart_url])
                        print(f"✅ {ticker} → Signal: {signal}, Sentiment: {sentiment}")
                    
                    # Write batch results to file
                    writer.writerows(results)
                    out_file.flush()  # Ensure data is written to disk
            
            # Now merge with ticker_data.csv if it exists
            if ticker_data_exists:
                self.merge_with_ticker_data(has_stockscores_columns)
                
            print(f"\n✅ Done! Data saved to {self.output_file}")
            if ticker_data_exists:
                print("✅ Data also merged into ticker_data.csv")
                
            return True
                
        except Exception as e:
            print(f"❌ Error during scraping process: {e}")
            return False
        finally:
            if self.should_close_driver:
                self.driver.quit()
                print("✅ Browser closed successfully")
    
    def merge_with_ticker_data(self, has_stockscores_columns):
        """Merge StockScores data with existing ticker_data.csv"""
        try:
            # Read StockScores data
            stockscores_data = {}
            with open(self.output_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stockscores_data[row['Ticker']] = {
                        'Signal Score': row['Signal Score'],
                        'Sentiment Score': row['Sentiment Score'],
                        'Screenshot': row['Screenshot']
                    }
            
            # Read existing ticker_data.csv
            ticker_data = []
            with open("ticker_data.csv", 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames.copy() if reader.fieldnames else []
                
                # Add StockScores columns if they don't exist
                if not has_stockscores_columns:
                    for col in ['Signal Score', 'Sentiment Score', 'Screenshot']:
                        if col not in fieldnames:
                            fieldnames.append(col)
                
                for row in reader:
                    ticker = row.get('ticker', '')
                    if ticker and ticker in stockscores_data:
                        row['Signal Score'] = stockscores_data[ticker]['Signal Score']
                        row['Sentiment Score'] = stockscores_data[ticker]['Sentiment Score']
                        row['Screenshot'] = stockscores_data[ticker]['Screenshot']
                    ticker_data.append(row)
            
            # Add any tickers from stockscores that aren't in ticker_data.csv
            existing_tickers = {row.get('ticker', '') for row in ticker_data}
            for ticker, data in stockscores_data.items():
                if ticker not in existing_tickers:
                    new_row = {'ticker': ticker}
                    new_row.update(data)
                    ticker_data.append(new_row)
            
            # Write updated data back to ticker_data.csv
            with open("ticker_data.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(ticker_data)
                
            print("✅ Successfully merged StockScores data with ticker_data.csv")
            return True
            
        except Exception as e:
            print(f"❌ Error merging data: {e}")
            return False

    def close(self):
        """Clean up resources if needed"""
        if self.should_close_driver:
            try:
                self.driver.quit()
                print("✅ Browser closed successfully")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")

if __name__ == "__main__":
    scraper = StockScoresScraper()
    try:
        scraper.run()
    finally:
        scraper.close()