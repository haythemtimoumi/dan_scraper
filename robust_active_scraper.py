#!/usr/bin/env python
"""
Robust active ticker scraper with improved browser management
"""

import psycopg2
import time
import subprocess
import os
import shutil
from datetime import datetime
from config.settings import DB_CONFIG

class RobustActiveScraper:
    def __init__(self):
        self.driver = None
        self.batch_size = 10  # Smaller batches to prevent resource exhaustion
        self.max_retries = 2  # Reduced retries
    
    def check_disk_space(self):
        """Check available disk space and clean up if needed"""
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (1024**3)
            free_percent = (free / total) * 100
            
            print(f"Disk space: {free_gb}GB free ({free_percent:.1f}%)")
            
            if free_percent < 5:  # Less than 5% free
                print("⚠️ Low disk space detected, cleaning up...")
                self.cleanup_browser_processes()
                # Clean logs older than 1 day
                subprocess.run(["find", "logs/", "-name", "*.log", "-mtime", "+1", "-delete"], capture_output=True, cwd="/root/dan_scraper")
                return False
            return True
        except:
            return True
        
    def cleanup_browser_processes(self):
        """Aggressively cleanup browser processes and temp files"""
        try:
            subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
            time.sleep(2)
            
            # Clean up Chrome temp directories to prevent disk space issues
            subprocess.run(["find", "/tmp", "-name", "tmp*", "-type", "d", "-mmin", "+30", "-exec", "rm", "-rf", "{}", "+"], capture_output=True)
            subprocess.run(["find", "/tmp", "-name", ".com.google.Chrome.*", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], capture_output=True)
            subprocess.run(["find", "/tmp", "-name", ".org.chromium.Chromium.*", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], capture_output=True)
        except:
            pass
    
    def init_browser(self):
        """Initialize browser with proper cleanup"""
        self.cleanup_browser_processes()
        
        for attempt in range(3):
            try:
                print(f"Initializing undetected Chrome browser...")
                from core.browser import get_driver
                self.driver = get_driver(headless=True, clear_cache=True)
                print("Chrome session started successfully")
                return True
            except Exception as e:
                print(f"Browser initialization attempt {attempt + 1} failed: {e}")
                if "No space left on device" in str(e):
                    print("Disk space issue detected, cleaning up...")
                    self.cleanup_browser_processes()
                    # Additional cleanup for disk space
                    subprocess.run(["rm", "-rf", "/tmp/tmp*"], capture_output=True)
                if attempt < 2:
                    print("Retrying in 3 seconds...")
                    time.sleep(3)
        
        print("Failed to initialize Chrome browser: No space left on device")
        print("Please ensure Chrome and ChromeDriver are properly installed and configured.")
        return False
    
    def close_browser(self):
        """Safely close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        self.cleanup_browser_processes()
    
    def scrape_stockscores_simple(self, ticker):
        """Simplified StockScores scraping with minimal DOM interaction"""
        if not self.driver:
            return "N/A", "N/A", "N/A"
            
        try:
            url = f"https://www.stockscores.com/charts/charts/?ticker={ticker}"
            self.driver.get(url)
            time.sleep(3)  # Fixed wait instead of WebDriverWait
            
            # Simple element finding without complex waits
            signal = "N/A"
            sentiment = "N/A" 
            chart_url = "N/A"
            
            try:
                signal_elem = self.driver.find_element("xpath", '//strong[contains(text(), "Signal")]/following::span[@style="font-size:24px;"]/b')
                signal = signal_elem.text.strip()
            except:
                pass
                
            try:
                sentiment_elem = self.driver.find_element("xpath", '//strong[contains(text(), "Sentiment")]/following::span[@style="font-size:24px;"]/b')
                sentiment = sentiment_elem.text.strip()
            except:
                pass
                
            try:
                img_elem = self.driver.find_element("xpath", '//div[@class="col_full"]/img')
                chart_url = img_elem.get_attribute("src")
            except:
                pass
            
            return signal, sentiment, chart_url
            
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")
            return "N/A", "N/A", "N/A"
    
    def fetch_price(self, ticker):
        """Fetch price from Yahoo Finance API"""
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'chart' in data and data['chart']['result']:
                    result = data['chart']['result'][0]
                    if 'meta' in result and 'regularMarketPrice' in result['meta']:
                        price = result['meta']['regularMarketPrice']
                        return round(float(price), 2) if price else None
        except:
            pass
        return None
    
    def process_batch(self, tickers_batch, conn, cursor):
        """Process a batch of tickers with fresh browser"""
        success_count = 0
        
        # Check disk space before processing
        if not self.check_disk_space():
            print("❌ Insufficient disk space, skipping batch")
            return 0
        
        # Initialize browser for this batch
        if not self.init_browser():
            print("Failed to initialize browser for batch")
            return 0
        
        try:
            for ticker_id, symbol, guru_id, list_type, last_action, per_portfolio in tickers_batch:
                try:
                    print(f"Processing {symbol}...")
                    
                    # Get Rule1 data from most recent record this month
                    cursor.execute("""
                        SELECT rule1_score, moat_score, management_score, buy_price, 
                               full_name, last_gr, long_gr, pbt
                        FROM stock_analysis 
                        WHERE ticker = %s AND rule1_score IS NOT NULL
                        AND date >= date_trunc('month', CURRENT_DATE)
                        ORDER BY date DESC LIMIT 1
                    """, (symbol,))
                    
                    rule1_data = cursor.fetchone()
                    if rule1_data:
                        rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = rule1_data
                    else:
                        rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = (None, None, None, None, None, None, None, None)
                    
                    # Get StockScores data with retry
                    signal_score = sentiment_score = screenshot = "N/A"
                    for attempt in range(self.max_retries):
                        try:
                            signal_score, sentiment_score, screenshot = self.scrape_stockscores_simple(symbol)
                            if signal_score != "N/A" or attempt == self.max_retries - 1:
                                break
                        except Exception as e:
                            print(f"StockScores attempt {attempt + 1} failed for {symbol}: {e}")
                            time.sleep(2)
                    
                    # Get price
                    price = self.fetch_price(symbol)
                    
                    # Calculate per_upside
                    per_upside = None
                    if buy_price and price and price > 0:
                        try:
                            buy_price_num = float(buy_price)
                            per_upside = round((2 * buy_price_num - price) / price * 100, 2)
                        except (ValueError, TypeError):
                            per_upside = None
                    
                    # Insert record
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        INSERT INTO stock_analysis (
                            ticker_id, guru_id, date, ticker, source,
                            rule1_score, moat_score, management_score, buy_price,
                            full_name, last_gr, long_gr, pbt,
                            signal_score, sentiment_score, screenshot,
                            last_price, last_action, per_portfolio, per_upside
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ticker_id, guru_id, current_time, symbol, list_type,
                        rule1_score, moat_score, management_score, buy_price,
                        full_name, last_gr, long_gr, pbt,
                        signal_score if signal_score != 'N/A' else None,
                        sentiment_score if sentiment_score != 'N/A' else None,
                        screenshot if screenshot != 'N/A' else None,
                        price, last_action, per_portfolio, str(per_upside) if per_upside is not None else None
                    ))
                    
                    conn.commit()
                    success_count += 1
                    print(f"✅ {symbol}: Rule1={rule1_score}, Signal={signal_score}, Price=${price}")
                    
                except Exception as e:
                    print(f"❌ Error processing {symbol}: {e}")
                    conn.rollback()
        
        finally:
            self.close_browser()
        
        return success_count
    
    def run(self):
        """Main execution method"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Starting robust active ticker process at {current_time}...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Get active tickers
            print("Querying for active tickers...")
            cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true")
            active_tickers = cursor.fetchall()
            
            print(f"Query returned {len(active_tickers)} active tickers")
            
            if not active_tickers:
                print("❌ No active tickers found")
                # Debug: check if there are any tickers at all
                cursor.execute("SELECT COUNT(*) FROM scraper_tasks")
                total_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM scraper_tasks WHERE active = true")
                active_count = cursor.fetchone()[0]
                print(f"Debug: Total tickers: {total_count}, Active tickers: {active_count}")
                return 0
            
            print(f"Processing {len(active_tickers)} active tickers in batches of {self.batch_size}...")
            
            total_success = 0
            
            # Process in batches
            for i in range(0, len(active_tickers), self.batch_size):
                batch = active_tickers[i:i+self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(active_tickers) - 1) // self.batch_size + 1
                
                print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} tickers)")
                
                batch_success = self.process_batch(batch, conn, cursor)
                total_success += batch_success
                
                print(f"Batch {batch_num} completed: {batch_success}/{len(batch)} successful")
                
                # Brief pause between batches
                if i + self.batch_size < len(active_tickers):
                    time.sleep(5)
            
            print(f"\n✅ Process completed: {total_success}/{len(active_tickers)} records created")
            
            # Send notifications
            try:
                from utils.email_notifier import send_completion_email
                send_completion_email(
                    recipient_email="dan.moore@tundraeng.com",
                    success_count=total_success,
                    total_count=len(active_tickers),
                    process_name="Robust Active Ticker Scraping"
                )
            except:
                pass
            
            try:
                from firebase_notifier import FirebaseNotifier
                FirebaseNotifier.send_notification(
                    title="Robust Scraper Complete",
                    body=f"Active ticker scraper finished: {total_success}/{len(active_tickers)} records",
                    data={"script": "robust_active_scraper", "success_count": str(total_success), "total_count": str(len(active_tickers)), "timestamp": str(datetime.now())}
                )
            except:
                pass
            
            return total_success
            
        finally:
            cursor.close()
            conn.close()
            self.cleanup_browser_processes()

if __name__ == "__main__":
    scraper = RobustActiveScraper()
    scraper.run()