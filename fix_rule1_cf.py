#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG
import time

def fix_rule1_cf_issue():
    """Skip Rule1 scraping and only use StockScores + Yahoo Finance"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, guru_id, list_type FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("❌ No active tickers found")
        return 0
    
    print(f"🎯 Processing {len(active_tickers)} tickers (StockScores + Yahoo only)")
    
    # Only use StockScores (no Rule1 due to CF)
    from scrapers.stockscores_scraper import StockScoresScraper
    
    stockscores_scraper = None
    
    try:
        stockscores_scraper = StockScoresScraper()
        print("✅ StockScores scraper initialized")
        
        today = datetime.now().strftime('%Y-%m-%d')
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type) in enumerate(active_tickers, 1):
            print(f"\n🔍 [{i}/{len(active_tickers)}] Processing {symbol}...")
            
            ticker_data = {
                'rule1_score': None, 'management_score': None, 'moat_score': None,
                'buy_price': None, 'full_name': None, 'last_gr': None,
                'long_gr': None, 'pbt': None, 'signal_score': None,
                'sentiment_score': None, 'screenshot': None, 'last_price': None
            }
            
            try:
                # StockScores data (works fine)
                print(f"📈 Scraping StockScores for {symbol}...")
                signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                ticker_data['signal_score'] = signal_score if signal_score != 'N/A' else None
                ticker_data['sentiment_score'] = sentiment_score if sentiment_score != 'N/A' else None
                ticker_data['screenshot'] = screenshot if screenshot != 'N/A' else None
                print(f"✅ StockScores: Signal={signal_score}, Sentiment={sentiment_score}")
                
                # Yahoo Finance price (works fine)
                print(f"💰 Fetching price for {symbol}...")
                ticker_data['last_price'] = fetch_price(symbol)
                print(f"✅ Price: {ticker_data['last_price']}")
                
                # Save to database
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        rule1_score, management_score, moat_score, buy_price, full_name,
                        last_gr, long_gr, pbt, signal_score, sentiment_score, screenshot, last_price
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, source, guru_id, date) DO UPDATE SET
                        signal_score = EXCLUDED.signal_score,
                        sentiment_score = EXCLUDED.sentiment_score,
                        screenshot = EXCLUDED.screenshot,
                        last_price = EXCLUDED.last_price
                """, (
                    ticker_id, guru_id, today, symbol, list_type,
                    None, None, None, None, None, None, None, None,
                    ticker_data['signal_score'], ticker_data['sentiment_score'], 
                    ticker_data['screenshot'], ticker_data['last_price']
                ))
                
                success_count += 1
                print(f"✅ [{success_count}/{len(active_tickers)}] Saved {symbol}")
                
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        conn.commit()
        print(f"\n🎉 Complete: {success_count}/{len(active_tickers)} successful")
        
    finally:
        if stockscores_scraper:
            stockscores_scraper.close()
    
    cursor.close()
    conn.close()
    return success_count

def fetch_price(ticker):
    """Fetch current price from Yahoo Finance"""
    try:
        import requests
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'chart' in data and data['chart']['result']:
            return data['chart']['result'][0]['meta']['regularMarketPrice']
    except:
        pass
    return None

if __name__ == "__main__":
    fix_rule1_cf_issue()