#!/usr/bin/env python
"""
Hourly process that creates complete records with:
1. Fresh StockScores data
2. Fresh Price data  
3. Reused Rule1 data from current month
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def run_hourly_process():
    """Run hourly process creating complete records per ticker"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Starting hourly process at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get active tickers with hourly scrape type
        cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true AND scrape_type = 'hourly'")
        active_tickers = cursor.fetchall()
        
        if not active_tickers:
            print("❌ No active tickers found")
            return 0
        
        print(f"Processing {len(active_tickers)} tickers...\n")
        
        # Initialize scrapers
        from scrapers.stockscores_scraper import StockScoresScraper
        stockscores_scraper = StockScoresScraper()
        
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(active_tickers, 1):
            print(f"[{i}/{len(active_tickers)}] Processing {symbol}...")
            
            try:
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
                
                # Get fresh StockScores data
                signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                
                # Get fresh Price data
                price = fetch_price(symbol)
                
                # Create complete record
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        rule1_score, moat_score, management_score, buy_price,
                        full_name, last_gr, long_gr, pbt,
                        signal_score, sentiment_score, screenshot,
                        last_price, last_action, per_portfolio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker_id, guru_id, current_time, symbol, list_type,
                    rule1_score, moat_score, management_score, buy_price,
                    full_name, last_gr, long_gr, pbt,
                    signal_score if signal_score != 'N/A' else None,
                    sentiment_score if sentiment_score != 'N/A' else None,
                    screenshot if screenshot != 'N/A' else None,
                    price, last_action, per_portfolio
                ))
                
                success_count += 1
                print(f"Complete record created: Rule1={rule1_score}, Signal={signal_score}, Price=${price}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        conn.commit()
        stockscores_scraper.close()
        
        print(f"\nHourly process completed: {success_count}/{len(active_tickers)} complete records created")
        print(f"Each record contains: Rule1 + StockScores + Price data")
        
    finally:
        cursor.close()
        conn.close()

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
    run_hourly_process()