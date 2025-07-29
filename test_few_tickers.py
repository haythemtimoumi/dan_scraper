#!/usr/bin/env python
"""
Test processing just a few tickers to debug Rule1 issues
"""
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def test_few_tickers():
    """Test processing just 3 tickers to debug issues"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Testing few tickers at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get just 3 active tickers for testing
        cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true AND scrape_status = 'pending' LIMIT 3")
        test_tickers = cursor.fetchall()
        
        if not test_tickers:
            print("No active tickers found")
            return 0
        
        print(f"Testing {len(test_tickers)} tickers...\n")
        
        # Initialize scrapers
        from scrapers.scores_scraper import TickerSearcher
        from scrapers.stockscores_scraper import StockScoresScraper
        from core.browser_stable import get_stable_driver
        
        print("Initializing shared browser session...")
        shared_driver = get_stable_driver(headless=True)
        
        rule1_searcher = TickerSearcher(driver=shared_driver)
        stockscores_scraper = StockScoresScraper(driver=shared_driver)
        
        # Login to Rule1
        print("Attempting Rule1 login...")
        login_result = rule1_searcher.login(auto_verify=True)
        
        if not login_result:
            print("❌ Rule1 login failed")
            return 0
        else:
            print("✅ Rule1 login successful - starting ticker processing...\n")
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(test_tickers, 1):
            print(f"[{i}/{len(test_tickers)}] Processing {symbol}...")
            
            # Test Rule1 data extraction
            from run_sequential_scraping import scrape_rule1_data
            rule1_data = scrape_rule1_data(rule1_searcher, symbol)
            print(f"Rule1 result: {rule1_data}")
            
            # Test StockScores data
            signal_score, sentiment_score, screenshot = stockscores_scraper.scrape_scores(symbol)
            print(f"StockScores result: Signal={signal_score}, Sentiment={sentiment_score}")
            
            # Test price fetch
            from run_sequential_scraping import fetch_price
            price = fetch_price(symbol)
            print(f"Price result: ${price}")
            
            print(f"✅ {symbol} complete\n")
        
        shared_driver.quit()
        print("✅ Test completed")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_few_tickers()