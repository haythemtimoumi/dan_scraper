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
    """Save Rule1 list tickers to scraper_tasks table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get or create guru for rule1
        cursor.execute("""
            INSERT INTO guru (guru_name, description) 
            VALUES (%s, %s) 
            ON CONFLICT (guru_name) DO NOTHING 
            RETURNING id
        """, ('rule1', 'Rule1 filtered stocks'))
        
        guru_result = cursor.fetchone()
        if guru_result:
            guru_id = guru_result[0]
        else:
            cursor.execute("SELECT id FROM guru WHERE guru_name = %s", ('rule1',))
            guru_id = cursor.fetchone()[0]
        
        for ticker in tickers:
            cursor.execute("""
                INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type, active, scrape_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, guru_id, list_type) 
                DO UPDATE SET 
                    active = TRUE,
                    scrape_status = CASE 
                        WHEN scraper_tasks.list_type = 'rule1_list' THEN 'pending'
                        ELSE scraper_tasks.scrape_status
                    END
            """, (ticker, guru_id, 'rule1_list', 'monthly', True, 'pending'))
        
        conn.commit()
        print(f"Saved {len(tickers)} tickers to database with guru='rule1' and list_type='rule1_list'")
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    scrape_rule1_list_to_db()