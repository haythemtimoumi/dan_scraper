#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG
import time

def fix_cf_scraper():
    """Fixed version that handles CF protection and processes all active tickers"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get active tickers
    cursor.execute("SELECT id, symbol, guru_id, list_type FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("❌ No active tickers found")
        return 0
    
    print(f"🎯 Found {len(active_tickers)} active tickers to process")
    
    # Initialize scrapers with CF bypass
    from scrapers.scores_scraper import TickerSearcher
    from scrapers.stockscores_scraper import StockScoresScraper
    
    rule1_searcher = None
    stockscores_scraper = None
    
    try:
        # Initialize Rule1 scraper with retry logic
        print("🔐 Initializing Rule1 scraper...")
        rule1_searcher = TickerSearcher()
        
        # Try login with retries for CF protection
        login_attempts = 3
        for attempt in range(login_attempts):
            print(f"🔑 Login attempt {attempt + 1}/{login_attempts}...")
            if rule1_searcher.login():
                print("✅ Rule1 login successful")
                break
            else:
                print(f"⚠️ Login attempt {attempt + 1} failed")
                if attempt < login_attempts - 1:
                    print("⏳ Waiting 10 seconds before retry...")
                    time.sleep(10)
        else:
            print("❌ All login attempts failed")
            return 0
        
        # Initialize StockScores scraper
        stockscores_scraper = StockScoresScraper()
        print("✅ StockScores scraper initialized")
        
        # Process each ticker
        today = datetime.now().strftime('%Y-%m-%d')
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type) in enumerate(active_tickers, 1):
            print(f"\n🔍 [{i}/{len(active_tickers)}] Processing {symbol}...")
            
            # Initialize data with defaults
            ticker_data = {
                'rule1_score': None, 'management_score': None, 'moat_score': None,
                'buy_price': None, 'full_name': None, 'last_gr': None,
                'long_gr': None, 'pbt': None, 'signal_score': None,
                'sentiment_score': None, 'screenshot': None, 'last_price': None
            }
            
            try:
                # Rule1 data with CF handling
                print(f"📊 Scraping Rule1 data for {symbol}...")
                rule1_data = scrape_rule1_with_cf_handling(rule1_searcher, symbol)
                if rule1_data:
                    ticker_data.update(rule1_data)
                    print(f"✅ Rule1 data collected for {symbol}")
                else:
                    print(f"⚠️ Rule1 data failed for {symbol}")
                
                # StockScores data
                print(f"📈 Scraping StockScores for {symbol}...")
                try:
                    signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                    ticker_data['signal_score'] = signal_score if signal_score != 'N/A' else None
                    ticker_data['sentiment_score'] = sentiment_score if sentiment_score != 'N/A' else None
                    ticker_data['screenshot'] = screenshot if screenshot != 'N/A' else None
                    print(f"✅ StockScores data collected for {symbol}")
                except Exception as e:
                    print(f"⚠️ StockScores error for {symbol}: {e}")
                
                # Current price
                print(f"💰 Fetching price for {symbol}...")
                try:
                    ticker_data['last_price'] = fetch_price_with_retry(symbol)
                    print(f"✅ Price: {ticker_data['last_price']}")
                except Exception as e:
                    print(f"⚠️ Price error for {symbol}: {e}")
                
                # Save to database
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        rule1_score, management_score, moat_score, buy_price, full_name,
                        last_gr, long_gr, pbt, signal_score, sentiment_score, screenshot, last_price
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, source, guru_id, date) DO UPDATE SET
                        rule1_score = EXCLUDED.rule1_score,
                        management_score = EXCLUDED.management_score,
                        moat_score = EXCLUDED.moat_score,
                        buy_price = EXCLUDED.buy_price,
                        full_name = EXCLUDED.full_name,
                        last_gr = EXCLUDED.last_gr,
                        long_gr = EXCLUDED.long_gr,
                        pbt = EXCLUDED.pbt,
                        signal_score = EXCLUDED.signal_score,
                        sentiment_score = EXCLUDED.sentiment_score,
                        screenshot = EXCLUDED.screenshot,
                        last_price = EXCLUDED.last_price
                """, (
                    ticker_id, guru_id, today, symbol, list_type,
                    ticker_data['rule1_score'], ticker_data['management_score'], ticker_data['moat_score'],
                    ticker_data['buy_price'], ticker_data['full_name'], ticker_data['last_gr'],
                    ticker_data['long_gr'], ticker_data['pbt'], ticker_data['signal_score'],
                    ticker_data['sentiment_score'], ticker_data['screenshot'], ticker_data['last_price']
                ))
                
                success_count += 1
                print(f"✅ [{success_count}/{len(active_tickers)}] Saved {symbol} to database")
                
                # Small delay between tickers to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        conn.commit()
        print(f"\n🎉 Processing complete: {success_count}/{len(active_tickers)} successful")
        
    finally:
        if rule1_searcher:
            rule1_searcher.close()
        if stockscores_scraper:
            stockscores_scraper.close()
    
    cursor.close()
    conn.close()
    return success_count

def scrape_rule1_with_cf_handling(searcher, symbol, max_retries=2):
    """Scrape Rule1 data with CF protection handling"""
    for attempt in range(max_retries):
        try:
            print(f"🔄 Rule1 attempt {attempt + 1}/{max_retries} for {symbol}")
            
            # Add delay for CF protection
            if attempt > 0:
                time.sleep(5)
            
            success = searcher._process_single_ticker(symbol)
            if not success:
                continue
            
            # Read data from CSV
            import csv, os
            csv_file = searcher.csv_file
            if not os.path.exists(csv_file):
                continue
            
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Find data for this ticker
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
        except Exception as e:
            print(f"⚠️ Rule1 attempt {attempt + 1} error: {e}")
    
    return None

def fetch_price_with_retry(ticker, max_retries=3):
    """Fetch price with retry logic"""
    import requests
    
    for attempt in range(max_retries):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            response = requests.get(url, timeout=10)
            data = response.json()
            if 'chart' in data and data['chart']['result']:
                return data['chart']['result'][0]['meta']['regularMarketPrice']
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"⚠️ Price fetch failed for {ticker}: {e}")
    
    return None

if __name__ == "__main__":
    fix_cf_scraper()