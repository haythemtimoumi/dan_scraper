#!/usr/bin/env python
"""
Script to change scrape_status to 'pending' for all active tickers
"""

import psycopg2
from config.settings import DB_CONFIG

def change_active_to_pending():
    """Change scrape_status to 'pending' where active = true"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Update scrape_status to pending for active tickers
        cursor.execute("""
            UPDATE scraper_tasks 
            SET scrape_status = 'pending'
            WHERE active = true
        """)
        
        # Get count of updated records
        updated_count = cursor.rowcount
        
        conn.commit()
        print(f"Successfully updated {updated_count} active tickers to 'pending' status")
        
    except Exception as e:
        print(f"Error updating scraper_tasks: {e}")
        conn.rollback()
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    change_active_to_pending()