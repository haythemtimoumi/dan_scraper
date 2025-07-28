#!/usr/bin/env python
"""
Monthly rule script that sets up scraper_tasks table for monthly scraping
"""

import psycopg2
from config.settings import DB_CONFIG

def setup_monthly_scraping():
    """Set all tickers to monthly scraping mode"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Update all tickers in scraper_tasks table
        cursor.execute("""
            UPDATE scraper_tasks 
            SET 
                active = false,
                current_step = 'rule1',
                scrape_status = 'not active'
        """)
        
        # Get count of updated records
        updated_count = cursor.rowcount
        
        conn.commit()
        print(f"Successfully updated {updated_count} tickers for monthly scraping")
        print("Settings applied:")
        print("- active = false")
        print("- current_step = rule1") 
        print("- scrape_status = not active")

        
    except Exception as e:
        print(f"Error updating scraper_tasks: {e}")
        conn.rollback()
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_monthly_scraping()