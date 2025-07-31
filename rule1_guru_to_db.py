#!/usr/bin/env python
import time
import psycopg2
from scrapers.rule1_scraper import Rule1Scraper
from scrapers.guru_scraper import GuruScraper
from config.settings import DB_CONFIG

def scrape_rule1_guru_to_db(auto_verify=True):
    """
    Login to Rule1Toolbox and scrape guru portfolios, save directly to scraper_tasks table
    """
    scraper = None
    
    try:
        # STEP 1: Login to Rule1Toolbox
        print("\nSTEP 1: Login to Rule1Toolbox")
        print("Starting browser in visible mode for debugging...")
        scraper = Rule1Scraper(headless=True)  # Make browser visible
        
        login_success = scraper.login(auto_verify=auto_verify)
        if not login_success:
            print("Login failed.")
            return
        
        print("Successfully logged in to Rule1Toolbox")
        
        # STEP 5.5: Run guru scraper
        print("\nSTEP 5.5: Run guru scraper")
        print("Starting guru scraper with timeout protection...")
        guru_scraper = GuruScraper(driver=scraper.driver)
        
        try:
            import signal
            import threading
            
            # Set up timeout for guru scraping (10 minutes max)
            timeout_seconds = 600
            scraping_completed = threading.Event()
            
            def guru_scraping_task():
                try:
                    # Navigate to guru page
                    print("Navigating to guru page...")
                    if guru_scraper.navigate_to_guru_page():
                        print("Successfully navigated to guru page")
                        # Scrape guru data
                        print("Starting guru data scraping...")
                        if guru_scraper.scrape_guru_list():
                            print("✅ Guru scraping completed successfully")
                            
                            # Save to database instead of files
                            print("Saving guru data to database...")
                            save_guru_data_to_db(guru_scraper.guru_data)
                            print("✅ Guru data saved to database")
                        else:
                            print("❌ Failed to scrape guru data")
                    else:
                        print("❌ Failed to navigate to guru page")
                except Exception as e:
                    print(f"❌ Error in guru scraping task: {e}")
                finally:
                    scraping_completed.set()
            
            # Start guru scraping in a separate thread
            scraping_thread = threading.Thread(target=guru_scraping_task)
            scraping_thread.daemon = True
            scraping_thread.start()
            
            # Wait for completion or timeout
            if scraping_completed.wait(timeout=timeout_seconds):
                print("✅ Guru scraping completed within timeout")
            else:
                print(f"⚠️ Guru scraping timed out after {timeout_seconds} seconds")
                print("Continuing with the rest of the pipeline...")
                
        except Exception as guru_error:
            print(f"❌ Error during guru scraping: {guru_error}")
        finally:
            try:
                guru_scraper.close()
            except:
                pass
            
    except Exception as e:
        print(f"Error during process: {e}")
    finally:
        if scraper:
            scraper.close()

def save_guru_data_to_db(guru_data):
    """Save guru data to scraper_tasks table with proper FK relations"""
    if not guru_data:
        print("No guru data to save")
        return
        
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        for data in guru_data:
            # Get or create guru
            cursor.execute("""
                INSERT INTO guru (guru_name, description) 
                VALUES (%s, %s) 
                ON CONFLICT (guru_name) DO NOTHING 
                RETURNING id
            """, (data['guru_name'], f"Portfolio for {data['guru_name']}"))
            
            guru_result = cursor.fetchone()
            if guru_result:
                guru_id = guru_result[0]
            else:
                cursor.execute("SELECT id FROM guru WHERE guru_name = %s", (data['guru_name'],))
                guru_id = cursor.fetchone()[0]
            
            # Insert into scraper_tasks with guru_id FK
            cursor.execute("""
                INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type, active, last_action, per_portfolio, scrape_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, guru_id, list_type) 
                DO UPDATE SET 
                    active = TRUE, 
                    last_action = EXCLUDED.last_action, 
                    per_portfolio = EXCLUDED.per_portfolio,
                    scrape_status = CASE 
                        WHEN scraper_tasks.list_type = 'guru_portfolio' THEN 'pending'
                        ELSE scraper_tasks.scrape_status
                    END
            """, (data['ticker'], guru_id, 'guru_portfolio', 'monthly', True, data['last_action'], data['performance'], 'pending'))
        
        conn.commit()
        print(f"Saved {len(guru_data)} guru portfolio entries to database")
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Rule1 guru portfolios to database")
    parser.add_argument("--manual-verify", action="store_true",
                        help="Manually verify email code instead of automatic verification")
    
    args = parser.parse_args()
    
    scrape_rule1_guru_to_db(auto_verify=not args.manual_verify)