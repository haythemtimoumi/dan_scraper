#!/usr/bin/env python
# Custom ticker scraper that reads from text file with symbol and source columns

import csv
import sys
from scrapers.scores_scraper import TickerSearcher
from scrapers.stockscores_scraper import StockScoresScraper
from simple_price_fetcher import fetch_all_prices
from merge_and_save import merge_and_save
from core.browser import get_driver

def read_ticker_file(file_path):
    """Read tickers from text file with symbol,source columns"""
    from utils.source_tracker import save_ticker_source
    
    tickers = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row['symbol'].strip() if 'symbol' in row else row['ticker'].strip()
                source = row.get('source', 'unknown').strip()
                if ticker:
                    tickers.append(ticker)
                    save_ticker_source(ticker, source)
        print(f"✅ Loaded {len(tickers)} tickers from {file_path}")
        return tickers
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

def run_custom_scraper(ticker_file, csv_output="fresh_ticker_data.csv"):
    """Run custom scraper with specific steps"""
    
    # Read tickers from file
    tickers = read_ticker_file(ticker_file)
    if not tickers:
        print("❌ No tickers found")
        return False
    
    # Create fresh_combined_tickers.txt for other scrapers
    with open('fresh_combined_tickers.txt', 'w') as f:
        for ticker in tickers:
            f.write(f"{ticker}\n")
    
    driver = None
    
    try:
        driver = get_driver(headless=True)
        # Step 1: Rule1 Login & Ticker Search
        print("\n🔐 STEP 1: Rule1 Login & Ticker Search")
        searcher = TickerSearcher(driver=driver, csv_file=csv_output)
        
        if not searcher.login():
            print("❌ Login failed")
            return False
        
        # Process tickers with browser restart on failure
        for i, ticker in enumerate(tickers):
            print(f"🔍 Processing {ticker} ({i+1}/{len(tickers)})...")
            try:
                searcher._process_single_ticker(ticker)
            except Exception as e:
                print(f"❌ Browser error for {ticker}: {e}")
                print("🔄 Restarting browser...")
                driver.quit()
                driver = get_driver(headless=True)
                searcher = TickerSearcher(driver=driver, csv_file=csv_output)
                if searcher.login():
                    searcher._process_single_ticker(ticker)
                else:
                    print(f"❌ Failed to restart for {ticker}")
        
        print("✅ Rule1 ticker search completed")
        
    except Exception as e:
        print(f"❌ Error in Rule1 scraping: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    # Step 2: StockScores Data
    print("\n📊 STEP 2: StockScores Data")
    try:
        stockscores_scraper = StockScoresScraper(input_file="fresh_combined_tickers.txt", output_file="fresh_stockscores_data.csv")
        stockscores_scraper.run()
        stockscores_scraper.close()
        print("✅ StockScores scraping completed")
    except Exception as e:
        print(f"❌ Error in StockScores scraping: {e}")
    
    # Step 3: Price Fetching
    print("\n💰 STEP 3: Price Fetching")
    try:
        fetch_all_prices()
        print("✅ Price fetching completed")
    except Exception as e:
        print(f"❌ Error fetching prices: {e}")
    
    # Step 4: Database Save
    print("\n💾 STEP 4: Database Save")
    try:
        merge_and_save()
        print("✅ Database save completed")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
    
    print("\n🎉 Custom scraping completed!")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Custom ticker scraper from text file")
    parser.add_argument("--ticker-file", required=True, help="Text file with symbol,source columns")
    parser.add_argument("--output", default="ticker_data.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    success = run_custom_scraper(args.ticker_file, args.output)
    sys.exit(0 if success else 1)