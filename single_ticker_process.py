#!/usr/bin/env python
"""
Single ticker demand process:
1. Manual ticker input
2. Fresh StockScores data
3. Fresh Price data  
4. Reused Rule1 data from current month
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def process_single_ticker():
    """Process a single ticker with manual input"""
    # Get ticker from user
    ticker = input("Enter ticker symbol: ").strip().upper()
    if not ticker:
        print("❌ No ticker provided")
        return
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Processing {ticker} at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get ticker info from scraper_tasks
        cursor.execute("SELECT id, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE symbol = %s", (ticker,))
        ticker_info = cursor.fetchone()
        
        if not ticker_info:
            print(f"❌ Ticker {ticker} not found in scraper_tasks")
            return
        
        ticker_id, guru_id, list_type, last_action, per_portfolio = ticker_info
        
        # Get Rule1 data from most recent record this month
        cursor.execute("""
            SELECT rule1_score, moat_score, management_score, buy_price, 
                   full_name, last_gr, long_gr, pbt
            FROM stock_analysis 
            WHERE ticker = %s AND rule1_score IS NOT NULL
            AND date >= date_trunc('month', CURRENT_DATE)
            ORDER BY date DESC LIMIT 1
        """, (ticker,))
        
        rule1_data = cursor.fetchone()
        if rule1_data:
            rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = rule1_data
            print(f"✓ Found Rule1 data: Score={rule1_score}")
        else:
            rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = (None, None, None, None, None, None, None, None)
            print("⚠ No Rule1 data found for current month")
        
        # Get fresh StockScores data
        from scrapers.stockscores_scraper import StockScoresScraper
        stockscores_scraper = StockScoresScraper()
        signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(ticker)
        stockscores_scraper.close()
        print(f"✓ StockScores data: Signal={signal_score}, Sentiment={sentiment_score}")
        
        # Get fresh Price data
        price = fetch_price(ticker)
        print(f"✓ Current price: ${price}")
        
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
            ticker_id, guru_id, current_time, ticker, list_type,
            rule1_score, moat_score, management_score, buy_price,
            full_name, last_gr, long_gr, pbt,
            signal_score if signal_score != 'N/A' else None,
            sentiment_score if sentiment_score != 'N/A' else None,
            screenshot if screenshot != 'N/A' else None,
            price, last_action, per_portfolio
        ))
        
        conn.commit()
        print(f"\n✅ Complete record created for {ticker}")
        
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
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
    process_single_ticker()