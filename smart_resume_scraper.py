#!/usr/bin/env python
# Smart resume script that automatically detects where scraping stopped and continues

import os
import csv
import sys
from scrapers.scores_scraper import TickerSearcher
from core.browser import get_driver

def get_processed_tickers(csv_file):
    """Get set of already processed tickers from CSV file"""
    processed = set()
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticker = row['ticker'].strip()
                    if ticker:
                        processed.add(ticker)
            print(f"✅ Found {len(processed)} already processed tickers")
        except Exception as e:
            print(f"⚠️ Error reading processed tickers: {e}")
    return processed

def get_all_tickers_from_sources():
    """Get all tickers from ticker_sources.csv in order"""
    all_tickers = []
    try:
        with open('data/ticker_sources.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row['ticker'].strip()
                if ticker:
                    all_tickers.append(ticker)
        print(f"✅ Found {len(all_tickers)} total tickers in sources")
        return all_tickers
    except Exception as e:
        print(f"❌ Error reading ticker sources: {e}")
        return []

def get_remaining_tickers(csv_file):
    """Get list of tickers that still need to be processed"""
    processed = get_processed_tickers(csv_file)
    all_tickers = get_all_tickers_from_sources()
    
    remaining = [ticker for ticker in all_tickers if ticker not in processed]
    
    if processed:
        last_processed = None
        for ticker in reversed(all_tickers):
            if ticker in processed:
                last_processed = ticker
                break
        print(f"📍 Last processed ticker: {last_processed}")
    
    print(f"🔍 Found {len(remaining)} tickers remaining to process")
    if remaining:
        print(f"📝 Next tickers to process: {remaining[:10]}")
    
    return remaining

def smart_resume_scraper(csv_file="ticker_data_fixed.csv", headless=True):
    """Smart resume scraper that continues from where it left off"""
    
    # Get remaining tickers
    remaining_tickers = get_remaining_tickers(csv_file)
    
    if not remaining_tickers:
        print("✅ All tickers have been processed!")
        return True
        
    print(f"\n🔄 Starting smart resume for {len(remaining_tickers)} remaining tickers...")
    
    # Create a new driver
    driver = get_driver(headless=headless)
    driver.set_page_load_timeout(300)
    
    try:
        # Create searcher with existing driver and CSV file
        searcher = TickerSearcher(driver=driver, csv_file=csv_file)
        
        # Login first
        print("🔐 Logging in...")
        if not searcher.login():
            print("❌ Login failed, cannot resume scraping")
            return False
            
        print("✅ Login successful, starting to process tickers...")
        
        # Process each remaining ticker
        success_count = 0
        failed_tickers = []
        
        for i, ticker in enumerate(remaining_tickers, 1):
            print(f"\n🔍 Processing {ticker} ({i}/{len(remaining_tickers)})...")
            try:
                if searcher._process_single_ticker(ticker):
                    success_count += 1
                    print(f"✅ Successfully processed {ticker}")
                else:
                    failed_tickers.append(ticker)
                    print(f"❌ Failed to process {ticker}")
            except Exception as e:
                failed_tickers.append(ticker)
                print(f"❌ Error processing {ticker}: {e}")
                
        print(f"\n📊 Processing Summary:")
        print(f"✅ Successful: {success_count}/{len(remaining_tickers)}")
        print(f"❌ Failed: {len(failed_tickers)}")
        
        if failed_tickers:
            print(f"📝 Failed tickers: {failed_tickers[:10]}")
            # Save failed tickers to a file for retry
            with open('failed_tickers.txt', 'w') as f:
                for ticker in failed_tickers:
                    f.write(f"{ticker}\n")
            print("💾 Failed tickers saved to failed_tickers.txt")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return False
    finally:
        # Close the driver
        try:
            driver.quit()
            print("✅ Browser closed")
        except:
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Smart resume scraper that continues from where it stopped")
    parser.add_argument("--csv-file", default="ticker_data_fixed.csv", help="CSV file to save results")
    parser.add_argument("--visible", action="store_true", help="Run with visible browser")
    args = parser.parse_args()
    
    print("🚀 Starting Smart Resume Scraper...")
    print(f"📁 Using CSV file: {args.csv_file}")
    print(f"👁️ Browser mode: {'Visible' if args.visible else 'Headless'}")
    
    # Run the scraper
    success = smart_resume_scraper(
        csv_file=args.csv_file,
        headless=not args.visible
    )
    
    if success:
        print("\n🎉 Smart resume scraping completed successfully!")
    else:
        print("\n❌ Smart resume scraping failed!")
        sys.exit(1)