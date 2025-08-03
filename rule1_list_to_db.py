#!/usr/bin/env python
import psycopg2
from scrapers.rule1_scraper import Rule1Scraper
from config.settings import DB_CONFIG

def scrape_rule1_list_to_db():
    """
    Login to Rule1Toolbox, navigate to stock scan, configure filters, scrape tickers and save to database
    """
    scraper = Rule1Scraper(clear_cache=True)
    
    try:
        # STEP 1: Login to Rule1Toolbox
        print("STEP 1: Login to Rule1Toolbox")
        login_success = scraper.login(auto_verify=True)
        if not login_success:
            print("❌ Login failed.")
            return
        
        # STEP 2: Navigate to Stock Scan page
        print("STEP 2: Navigate to Stock Scan page")
        nav_success = scraper.navigate_to_stock_scan()
        if not nav_success:
            print("❌ Navigation to Stock Scan page failed.")
            return
            
        # STEP 3: Configure Rule One Scores
        print("STEP 3: Configure Rule One Scores")
        config_success = scraper.configure_rule_one_scores()
        if not config_success:
            print("⚠️ Configuration of Rule One Scores section failed. Continuing anyway...")
        
        # STEP 4: Apply filter and scrape tickers
        print("STEP 4: Apply filter and scrape tickers")
        filter_success = scraper.apply_filter()
        if not filter_success:
            print("⚠️ There was an issue applying the filter, but continuing anyway")
        
        print("🔍 Scraping ticker symbols...")
        tickers = scraper.scrape_only_tickers()
        
        if tickers:
            print(f"Found {len(tickers)} ticker symbols")
            # Save to database
            save_rule1_list_to_db(tickers)
        else:
            print("No ticker symbols found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

def save_rule1_list_to_db(tickers):
    """Save Rule1 list tickers to scraper_tasks table with guru mapping"""
    from utils.db_helpers import bulk_insert_tickers_with_guru_map
    
    tickers_data = [{
        'symbol': ticker,
        'guru_name': 'dan',
        'list_type': 'rule1',
        'scrape_type': 'monthly',
        'active': True,
        'scrape_status': 'pending'
    } for ticker in tickers]
    
    total, new, updated = bulk_insert_tickers_with_guru_map(tickers_data)
    print(f"Saved {total} tickers with guru='dan' and list_type='rule1': {new} new, {updated} updated")

if __name__ == "__main__":
    scrape_rule1_list_to_db()