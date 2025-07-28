#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def scrape_rule1_only():
    """Scrape Rule1 data for all active tickers and update rule1_scraped_at"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("❌ No active tickers found")
        return 0
    
    print(f"🎯 Rule1 scraping for {len(active_tickers)} tickers")
    
    from scrapers.scores_scraper import TickerSearcher
    
    rule1_searcher = None
    try:
        rule1_searcher = TickerSearcher()
        if not rule1_searcher.login():
            print("❌ Rule1 login failed")
            return 0
        
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(active_tickers, 1):
            print(f"\n🔍 [{i}/{len(active_tickers)}] Rule1 scraping {symbol}...")
            
            try:
                rule1_data = scrape_rule1_data(rule1_searcher, symbol)
                if rule1_data:
                    # Save to stock_analysis
                    cursor.execute("""
                        INSERT INTO stock_analysis (
                            ticker_id, guru_id, date, ticker, source,
                            rule1_score, management_score, moat_score, buy_price, full_name,
                            last_gr, long_gr, pbt, last_action, per_portfolio
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ticker_id, guru_id, current_timestamp, symbol, list_type,
                        rule1_data['rule1_score'], rule1_data['management_score'], 
                        rule1_data['moat_score'], rule1_data['buy_price'], 
                        rule1_data['full_name'], rule1_data['last_gr'], 
                        rule1_data['long_gr'], rule1_data['pbt'], last_action, per_portfolio
                    ))
                    
                    # Update rule1_scraped_at timestamp
                    cursor.execute("""
                        UPDATE scraper_tasks 
                        SET rule1_scraped_at = %s 
                        WHERE id = %s
                    """, (now, ticker_id))
                    
                    success_count += 1
                    print(f"✅ Rule1 data saved for {symbol}")
                else:
                    print(f"⚠️ Rule1 scraping failed for {symbol}")
                    
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        conn.commit()
        print(f"\n🎉 Rule1 complete: {success_count}/{len(active_tickers)} successful")
        
    finally:
        if rule1_searcher:
            rule1_searcher.close()
    
    cursor.close()
    conn.close()
    return success_count

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
        print(f"⚠️ Rule1 data extraction error for {symbol}: {e}")
        return None

if __name__ == "__main__":
    scrape_rule1_only()