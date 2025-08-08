#!/usr/bin/env python
"""
Daily fresh data scraper that creates complete records with:
1. Fresh Rule1 data
2. Fresh StockScores data
3. Fresh Price data
Only processes tickers where scrape_type = 'daily'
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG
import re

def run_daily_fresh_scraping():
    """Run complete fresh scraping for daily tickers only"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Starting daily fresh scraping process at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get active tickers with scrape_type = 'daily'
        cursor.execute("""
            SELECT DISTINCT ON (st.id) st.id, st.symbol, st.guru_id, st.list_type, gtm.last_act, gtm.per_port 
            FROM scraper_tasks st 
            JOIN guru_ticker_map gtm ON st.id = gtm.scraper_task_id 
            WHERE st.active = true AND st.scrape_type = 'daily'
            ORDER BY st.id, gtm.id
        """)
        daily_tickers = cursor.fetchall()
        
        if not daily_tickers:
            print("No daily tickers found")
            return 0
        
        print(f"Processing {len(daily_tickers)} daily tickers...\n")
        
        # Initialize scrapers
        from scrapers.scores_scraper import TickerSearcher
        from scrapers.stockscores_scraper import StockScoresScraper
        
        try:
            from core.browser_stable import get_stable_driver
            print("Initializing shared browser session...")
            shared_driver = get_stable_driver(headless=True)
            
            rule1_searcher = TickerSearcher(driver=shared_driver)
            stockscores_scraper = StockScoresScraper(driver=shared_driver)
            
            print("Attempting Rule1 login...")
            login_result = rule1_searcher.login(auto_verify=True)
            
            if not login_result:
                print("❌ Rule1 login failed")
                return 0
            else:
                print("✅ Rule1 login successful")
                
        except Exception as e:
            print(f"❌ Error initializing scrapers: {e}")
            return 0
        
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(daily_tickers, 1):
            print(f"[{i}/{len(daily_tickers)}] Processing {symbol}...")
            
            try:
                # Get fresh Rule1 data (skip ETFs)
                rule1_data = None
                if not is_etf(symbol):
                    rule1_data = scrape_rule1_data(rule1_searcher, symbol)
                    if rule1_data:
                        cursor.execute("UPDATE scraper_tasks SET rule1_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                else:
                    print(f"  → Skipping Rule1 for ETF: {symbol}")
                
                # Get fresh StockScores data
                signal_score, sentiment_score, screenshot = "N/A", "N/A", "N/A"
                try:
                    signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                    cursor.execute("UPDATE scraper_tasks SET stockscore_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                except Exception as e:
                    print(f"Warning: StockScores failed for {symbol}: {e}")
                
                # Get fresh Price data
                price = None
                try:
                    price = fetch_price(symbol)
                    cursor.execute("UPDATE scraper_tasks SET last_price_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                except Exception as e:
                    print(f"Warning: Price failed for {symbol}: {e}")
                
                # Calculate per_upside
                per_upside = None
                if rule1_data and rule1_data['buy_price'] and price:
                    try:
                        buy_price = rule1_data['buy_price']
                        per_upside = ((buy_price * 2 - price) / price) * 100
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
                
                cursor.execute("UPDATE scraper_tasks SET last_updated_at = %s WHERE id = %s", (current_time, ticker_id))
                
                success_count += 1
                print(f"Complete record created: Rule1={rule1_data['rule1_score'] if rule1_data else 'N/A'}, Signal={signal_score}, Price=${price}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        conn.commit()
        
        try:
            if 'shared_driver' in locals():
                shared_driver.quit()
                print("✅ Browser session closed")
        except Exception as e:
            print(f"Warning: Error closing browser: {e}")
        
        print(f"\nDaily fresh scraping completed: {success_count}/{len(daily_tickers)} complete records created")
        
    finally:
        cursor.close()
        conn.close()

def scrape_rule1_data(searcher, symbol):
    """Extract Rule1 data for a ticker"""
    try:
        print(f"  → Processing Rule1 for {symbol}...")
        success = searcher._process_single_ticker(symbol)
        if not success:
            return None
        
        import csv, os
        csv_file = searcher.csv_file
        if not os.path.exists(csv_file):
            return None
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for row in reversed(rows):
            if row['ticker'] == symbol:
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
        return None
    except Exception as e:
        print(f"  ❌ Rule1 error for {symbol}: {e}")
        return None

def clean_price_string(price_str):
    """Remove $ symbol and convert to float"""
    if not price_str or price_str == 'N/A':
        return None
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
    run_daily_fresh_scraping()