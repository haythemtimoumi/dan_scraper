#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def merge_and_save():
    """Get active tickers from scraper_tasks, scrape data, and save to stock_analysis"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get active tickers
    cursor.execute("SELECT id, symbol, guru_id, list_type FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("No active tickers found")
        return 0
    
    tickers = [row[1] for row in active_tickers]
    print(f"Found {len(tickers)} active tickers: {tickers}")
    
    # Initialize scrapers ONCE for all tickers
    from scrapers.scores_scraper import TickerSearcher
    from scrapers.stockscores_scraper import StockScoresScraper
    
    rule1_searcher = None
    stockscores_scraper = None
    
    try:
        # Login to Rule1 once
        rule1_searcher = TickerSearcher()
        if not rule1_searcher.login():
            print("❌ Failed to login to Rule1")
            return 0
            
        # Initialize StockScores scraper once
        stockscores_scraper = StockScoresScraper()
        print(f"✅ Initialized StockScores scraper")
        
        # Scrape data for each ticker and save to stock_analysis
        today = datetime.now().strftime('%Y-%m-%d')
        success_count = 0
        
        for ticker_id, symbol, guru_id, list_type in active_tickers:
            print(f"\n🔍 Processing ticker {symbol} (ID: {ticker_id}, Guru ID: {guru_id}, Type: {list_type})...")
            
            # Initialize data dictionary with defaults
            ticker_data = {
                'rule1_score': None,
                'management_score': None, 
                'moat_score': None,
                'buy_price': None,
                'full_name': None,
                'last_gr': None,
                'long_gr': None,
                'pbt': None,
                'signal_score': None,
                'sentiment_score': None,
                'screenshot': None,
                'last_price': None
            }
            
            try:
                # Scrape Rule1 data using existing session
                print(f"📊 Starting Rule1 scraping for {symbol}...")
                
                rule1_data = scrape_rule1_comprehensive(rule1_searcher, symbol)
                    
                print(f"📊 Rule1 scraping completed for {symbol}, got data: {rule1_data is not None}")
                if rule1_data:
                    ticker_data.update(rule1_data)
                    print(f"✅ Rule1 data scraped for {symbol}")
                else:
                    print(f"⚠️ Failed to scrape Rule1 data for {symbol}")
                
                # Scrape StockScores data
                print(f"📈 Scraping StockScores data for {symbol}...")
                try:
                    signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                    ticker_data['signal_score'] = signal_score if signal_score != 'N/A' else None
                    ticker_data['sentiment_score'] = sentiment_score if sentiment_score != 'N/A' else None
                    ticker_data['screenshot'] = screenshot if screenshot != 'N/A' else None
                    print(f"✅ StockScores data scraped for {symbol}")
                except Exception as e:
                    print(f"⚠️ Error scraping StockScores for {symbol}: {e}")
                
                # Fetch current price
                print(f"💰 Fetching current price for {symbol}...")
                try:
                    ticker_data['last_price'] = fetch_price(symbol)
                    print(f"✅ Price fetched for {symbol}: {ticker_data['last_price']}")
                except Exception as e:
                    print(f"⚠️ Error fetching price for {symbol}: {e}")
                    ticker_data['last_price'] = None
                
                # Save comprehensive data to stock_analysis
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
                print(f"✅ Saved comprehensive data for {symbol} to database")
                
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
        conn.commit()
        print(f"\n🎉 Database transaction committed successfully")
        
    finally:
        # Close scrapers only at the end
        if rule1_searcher:
            rule1_searcher.close()
        if stockscores_scraper:
            stockscores_scraper.close()
            
    cursor.close()
    conn.close()
    
    print(f"\n📊 Final Results: Successfully processed {success_count}/{len(active_tickers)} tickers")
    return success_count

def scrape_rule1_comprehensive(searcher, symbol):
    """Extract comprehensive Rule1 data for a specific ticker with timeout"""
    import signal
    import time
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Timeout processing {symbol}")
    
    try:
        print(f"🔍 Processing Rule1 data for {symbol}...")
        
        # Set a 90 second timeout for Windows compatibility
        start_time = time.time()
        max_time = 90
        
        try:
            success = searcher._process_single_ticker(symbol)
            elapsed = time.time() - start_time
            if elapsed > max_time:
                print(f"⏰ Processing {symbol} took too long ({elapsed:.1f}s), skipping")
                return None
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed > max_time:
                print(f"⏰ Timeout processing {symbol} after {elapsed:.1f}s")
                return None
            raise e
            
        if not success:
            print(f"❌ Failed to process {symbol} in Rule1")
            return None
            
        # Read the data from the CSV file that was just written
        import csv
        import os
        
        csv_file = searcher.csv_file
        if not os.path.exists(csv_file):
            print(f"❌ CSV file {csv_file} not found")
            return None
            
        # Read the last entry for this ticker
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Find the row for this ticker (should be the last one)
        for row in reversed(rows):
            if row['ticker'] == symbol:
                print(f"✅ Found Rule1 data for {symbol}")
                return {
                    'rule1_score': int(row['rule1_score']) if row['rule1_score'] != 'N/A' else None,
                    'management_score': int(row['management_score']) if row['management_score'] != 'N/A' else None,
                    'moat_score': int(row['moat_score']) if row['moat_score'] != 'N/A' else None,
                    'buy_price': row['buy_price'] if row['buy_price'] != 'N/A' else None,
                    'full_name': row['full_name'] if row['full_name'] != 'N/A' else None,
                    'last_gr': row['last_gr'] if row['last_gr'] != 'N/A' else None,
                    'long_gr': row['long_gr'] if row['long_gr'] != 'N/A' else None,
                    'pbt': row['guru'] if row['guru'] != 'N/A' else None  # 'guru' column contains PBT data
                }
                
        print(f"❌ No data found for {symbol} in CSV")
        return None
        
    except Exception as e:
        print(f"❌ Error extracting Rule1 data for {symbol}: {e}")
        return None

def fetch_price(ticker):
    """Fetch current price for ticker"""
    try:
        import requests
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(url)
        data = response.json()
        if 'chart' in data and data['chart']['result']:
            return data['chart']['result'][0]['meta']['regularMarketPrice']
    except:
        return None

if __name__ == "__main__":
    merge_and_save()