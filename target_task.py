#!/usr/bin/env python
"""
Target scraper that creates complete records with:
1. Fresh Rule1 data
2. Fresh StockScores data
3. Fresh Price data
All combined into single records per ticker (TARGET TICKERS ONLY)
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG
import re

def run_target_scraping():
    """Run complete scraping creating one record per ticker with all data (target tickers only)"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Starting target scraping process at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get target tickers
        cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE target = true AND scrape_status = 'pending'")
        target_tickers = cursor.fetchall()
        
        if not target_tickers:
            print("No target tickers found")
            return 0
        
        print(f"Processing {len(target_tickers)} target tickers...\n")
        
        # Initialize scrapers with error handling
        from scrapers.scores_scraper import TickerSearcher
        from scrapers.stockscores_scraper import StockScoresScraper
        
        rule1_searcher = None
        stockscores_scraper = None
        
        try:
            # Use single stable browser session for both scrapers
            from core.browser_stable import get_stable_driver
            print("Initializing shared browser session...")
            shared_driver = get_stable_driver(headless=True)
            
            rule1_searcher = TickerSearcher(driver=shared_driver)
            stockscores_scraper = StockScoresScraper(driver=shared_driver)
            
            # Login to Rule1 with optimized auto verification
            print("Attempting Rule1 login...")
            login_result = rule1_searcher.login(auto_verify=True)
            
            if not login_result:
                print("❌ Rule1 login failed - check credentials and email verification")
                return 0
            else:
                print("✅ Rule1 login successful - starting ticker processing...")
                
        except Exception as e:
            print(f"❌ Error initializing scrapers: {e}")
            return 0
        
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(target_tickers, 1):
            print(f"[{i}/{len(target_tickers)}] Processing {symbol}...")
            
            try:
                # Get Rule1 data with enhanced error handling and retry
                rule1_data = None
                max_rule1_retries = 2
                for rule1_attempt in range(max_rule1_retries):
                    try:
                        rule1_data = scrape_rule1_data(rule1_searcher, symbol)
                        if rule1_data:
                            cursor.execute("UPDATE scraper_tasks SET rule1_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                            break
                        else:
                            print(f"Rule1 attempt {rule1_attempt + 1} returned no data for {symbol}")
                    except Exception as e:
                        print(f"Rule1 attempt {rule1_attempt + 1} failed for {symbol}: {e}")
                    
                    if rule1_attempt < max_rule1_retries - 1:
                        print(f"Retrying Rule1 for {symbol} in 2 seconds...")
                        import time
                        time.sleep(2)
                
                if not rule1_data:
                    print(f"⚠️ All Rule1 attempts failed for {symbol} - ticker may not exist in Rule1Toolbox (ETF/Index fund?)")
                    print(f"  → Continuing with StockScores and price data for {symbol}...")
                
                # Get StockScores data with error handling
                signal_score, sentiment_score, screenshot = "N/A", "N/A", "N/A"
                try:
                    signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                    cursor.execute("UPDATE scraper_tasks SET stockscore_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                except Exception as e:
                    print(f"Warning: StockScores data failed for {symbol}: {e}")
                
                # Get Price data with error handling
                price = None
                try:
                    price = fetch_price(symbol)
                    cursor.execute("UPDATE scraper_tasks SET last_price_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                except Exception as e:
                    print(f"Warning: Price data failed for {symbol}: {e}")
                
                # Calculate per_upside
                per_upside = None
                if rule1_data and rule1_data['buy_price'] and price:
                    try:
                        buy_price = rule1_data['buy_price']
                        per_upside = (buy_price * 2 - price) / price
                    except (TypeError, ZeroDivisionError):
                        per_upside = None
                
                # Create complete record
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        rule1_score, management_score, moat_score, buy_price, full_name,
                        last_gr, long_gr, pbt,
                        signal_score, sentiment_score, screenshot,
                        last_price, last_action, per_portfolio, per_upside
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker_id, guru_id, current_time, symbol, list_type,
                    rule1_data['rule1_score'] if rule1_data else None,
                    rule1_data['management_score'] if rule1_data else None,
                    rule1_data['moat_score'] if rule1_data else None,
                    rule1_data['buy_price'] if rule1_data else None,
                    rule1_data['full_name'] if rule1_data else None,
                    rule1_data['last_gr'] if rule1_data else None,
                    rule1_data['long_gr'] if rule1_data else None,
                    rule1_data['pbt'] if rule1_data else None,
                    signal_score if signal_score != 'N/A' else None,
                    sentiment_score if sentiment_score != 'N/A' else None,
                    screenshot if screenshot != 'N/A' else None,
                    price, last_action, per_portfolio, per_upside
                ))
                
                # Update final timestamp
                cursor.execute("UPDATE scraper_tasks SET last_updated_at = %s WHERE id = %s", (current_time, ticker_id))
                
                success_count += 1
                print(f"Complete record created: Rule1={rule1_data['rule1_score'] if rule1_data else 'N/A'}, Signal={signal_score}, Price=${price}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        conn.commit()
        
        # Close shared browser session
        try:
            if 'shared_driver' in locals():
                shared_driver.quit()
                print("✅ Shared browser session closed")
        except Exception as e:
            print(f"Warning: Error closing shared browser: {e}")
        
        print(f"\nTarget scraping completed: {success_count}/{len(target_tickers)} complete records created")
        print(f"Each record contains: Rule1 + StockScores + Price data")
        
    finally:
        cursor.close()
        conn.close()

def scrape_rule1_data(searcher, symbol):
    """Extract Rule1 data for a ticker with detailed logging"""
    try:
        print(f"  → Processing Rule1 for {symbol}...")
        success = searcher._process_single_ticker(symbol)
        if not success:
            print(f"  ⚠️ Rule1 processing failed for {symbol}")
            return None
        
        import csv, os
        csv_file = searcher.csv_file
        if not os.path.exists(csv_file):
            print(f"  ⚠️ CSV file not found: {csv_file}")
            return None
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"  → Searching for {symbol} in {len(rows)} CSV rows...")
        for row in reversed(rows):
            if row['ticker'] == symbol:
                print(f"  ✅ Found Rule1 data for {symbol}")
                return {
                    'rule1_score': int(row['rule1_score']) if row['rule1_score'] != 'N/A' else None,
                    'management_score': int(row['management_score']) if row['management_score'] != 'N/A' else None,
                    'moat_score': int(row['moat_score']) if row['moat_score'] != 'N/A' else None,
                    'buy_price': clean_price_string(row['buy_price']),
                    'full_name': row['full_name'] if row['full_name'] != 'N/A' else None,
                    'last_gr': row['last_gr'] if row['last_gr'] != 'N/A' else None,
                    'long_gr': row['long_gr'] if row['long_gr'] != 'N/A' else None,
                    'pbt': row['guru'] if row['guru'] != 'N/A' else None
                }
        
        print(f"  ⚠️ {symbol} not found in CSV data")
        return None
    except Exception as e:
        print(f"  ❌ Rule1 data extraction error for {symbol}: {e}")
        return None

def clean_price_string(price_str):
    """Remove $ symbol and convert to float"""
    if not price_str or price_str == 'N/A':
        return None
    # Remove $ symbol and any whitespace, then convert to float
    cleaned = re.sub(r'[\$\s,]', '', str(price_str))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def fetch_price(ticker):
    """Fetch current price from Yahoo Finance"""
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

if __name__ == "__main__":
    run_target_scraping()