#!/usr/bin/env python
"""
Sequential scraper that creates complete records with:
1. Fresh Rule1 data
2. Fresh StockScores data
3. Fresh Price data
All combined into single records per ticker
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def run_sequential_scraping():
    """Run complete scraping creating one record per ticker with all data"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Starting sequential scraping process at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get active tickers
        cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true AND scrape_status = 'pending'")
        active_tickers = cursor.fetchall()
        
        if not active_tickers:
            print("No active tickers found")
            return 0
        
        print(f"Processing {len(active_tickers)} tickers...\n")
        
        # Initialize scrapers
        from scrapers.scores_scraper import TickerSearcher
        from scrapers.stockscores_scraper import StockScoresScraper
        
        rule1_searcher = TickerSearcher()
        stockscores_scraper = StockScoresScraper()
        
        # Login to Rule1
        print("Attempting Rule1 login...")
        login_result = rule1_searcher.login()
        print(f"Login result: {login_result}")
        print(f"Current URL after login attempt: {rule1_searcher.driver.current_url}")
        
        if not login_result:
            print("❌ Rule1 login failed")
            return 0
        else:
            print("✅ Rule1 login successful")
        
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(active_tickers, 1):
            print(f"[{i}/{len(active_tickers)}] Processing {symbol}...")
            
            try:
                # Get Rule1 data
                rule1_data = scrape_rule1_data(rule1_searcher, symbol)
                cursor.execute("UPDATE scraper_tasks SET rule1_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                
                # Get StockScores data
                signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                cursor.execute("UPDATE scraper_tasks SET stockscore_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                
                # Get Price data
                price = fetch_price(symbol)
                cursor.execute("UPDATE scraper_tasks SET last_price_scraped_at = %s WHERE id = %s", (current_time, ticker_id))
                
                # Create complete record
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        rule1_score, management_score, moat_score, buy_price, full_name,
                        last_gr, long_gr, pbt,
                        signal_score, sentiment_score, screenshot,
                        last_price, last_action, per_portfolio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    price, last_action, per_portfolio
                ))
                
                # Update final timestamp
                cursor.execute("UPDATE scraper_tasks SET last_updated_at = %s WHERE id = %s", (current_time, ticker_id))
                
                success_count += 1
                print(f"Complete record created: Rule1={rule1_data['rule1_score'] if rule1_data else 'N/A'}, Signal={signal_score}, Price=${price}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        conn.commit()
        rule1_searcher.close()
        stockscores_scraper.close()
        
        print(f"\nSequential scraping completed: {success_count}/{len(active_tickers)} complete records created")
        print(f"Each record contains: Rule1 + StockScores + Price data")
        
    finally:
        cursor.close()
        conn.close()

def scrape_rule1_data(searcher, symbol):
    """Extract Rule1 data for a ticker"""
    try:
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
                    'buy_price': row['buy_price'] if row['buy_price'] != 'N/A' else None,
                    'full_name': row['full_name'] if row['full_name'] != 'N/A' else None,
                    'last_gr': row['last_gr'] if row['last_gr'] != 'N/A' else None,
                    'long_gr': row['long_gr'] if row['long_gr'] != 'N/A' else None,
                    'pbt': row['guru'] if row['guru'] != 'N/A' else None
                }
        return None
    except Exception as e:
        print(f"Rule1 data extraction error for {symbol}: {e}")
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
    run_sequential_scraping()