#!/usr/bin/env python
# Rule1 ticker discovery script - scrapes tickers and saves with manual source

import os
import time
from scrapers.rule1_scraper import Rule1Scraper
from utils.source_tracker import save_ticker_source

def discover_rule1_tickers(output_file="manual_tickers.txt", auto_verify=True):
    """
    Discover tickers from Rule1 and save with manual source
    """
    print("🚀 Starting Rule1 ticker discovery...")
    
    scraper = None
    try:
        # Create Rule1Scraper instance
        scraper = Rule1Scraper()
        
        # Step 1: Login to Rule1Toolbox
        print("\n🔐 STEP 1: Rule1Toolbox Login")
        if not scraper.login(auto_verify=auto_verify):
            print("❌ Login failed")
            return False
        
        # Step 2: Navigate to Stock Scan
        print("\n📋 STEP 2: Navigate to Stock Scan")
        if not scraper.navigate_to_stock_scan():
            print("❌ Navigation failed")
            return False
        
        # Step 3: Configure Rule One Scores
        print("\n📋 STEP 3: Configure Rule One Scores")
        scraper.configure_rule_one_scores()
        
        # Step 4: Apply Filter & Scrape Tickers
        print("\n📋 STEP 4: Apply Filter & Scrape Tickers")
        scraper.apply_filter()
        tickers = scraper.scrape_only_tickers()
        
        if not tickers:
            print("❌ No tickers found")
            return False
        
        # Step 5: Save tickers with manual source
        print(f"\n💾 STEP 5: Saving {len(tickers)} tickers with manual source")
        with open(output_file, 'w') as f:
            f.write("ticker,source\n")
            for ticker in tickers:
                f.write(f"{ticker},manual\n")
                save_ticker_source(ticker, 'manual')
        
        print(f"✅ Saved {len(tickers)} tickers to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Discover Rule1 tickers and save with manual source")
    parser.add_argument("--output", default="manual_tickers.txt", help="Output file")
    parser.add_argument("--manual-verify", action="store_true", help="Manual email verification")
    
    args = parser.parse_args()
    
    success = discover_rule1_tickers(
        output_file=args.output,
        auto_verify=not args.manual_verify
    )
    
    if success:
        print(f"\n🎉 Discovery completed! Check {args.output}")
    else:
        print("\n❌ Discovery failed")