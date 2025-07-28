#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def scrape_stockscores_only():
    """Scrape StockScores data for all active tickers and update stockscore_scraped_at"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("❌ No active tickers found")
        return 0
    
    print(f"🎯 StockScores scraping for {len(active_tickers)} tickers")
    
    from scrapers.stockscores_scraper import StockScoresScraper
    
    stockscores_scraper = None
    try:
        stockscores_scraper = StockScoresScraper()
        
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(active_tickers, 1):
            print(f"\n📈 [{i}/{len(active_tickers)}] StockScores scraping {symbol}...")
            
            try:
                signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
                
                # Save to stock_analysis
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        signal_score, sentiment_score, screenshot,
                        last_action, per_portfolio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker_id, guru_id, current_timestamp, symbol, list_type,
                    signal_score if signal_score != 'N/A' else None,
                    sentiment_score if sentiment_score != 'N/A' else None,
                    screenshot if screenshot != 'N/A' else None,
                    last_action, per_portfolio
                ))
                
                # Update stockscore_scraped_at timestamp
                cursor.execute("""
                    UPDATE scraper_tasks 
                    SET stockscore_scraped_at = %s 
                    WHERE id = %s
                """, (now, ticker_id))
                
                success_count += 1
                print(f"✅ StockScores data saved for {symbol}: Signal={signal_score}, Sentiment={sentiment_score}")
                
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        conn.commit()
        print(f"\n🎉 StockScores complete: {success_count}/{len(active_tickers)} successful")
        
    finally:
        if stockscores_scraper:
            stockscores_scraper.close()
    
    cursor.close()
    conn.close()
    return success_count

if __name__ == "__main__":
    scrape_stockscores_only()