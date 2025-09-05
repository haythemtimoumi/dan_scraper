#!/usr/bin/env python
import psycopg2
from config.settings import DB_CONFIG

def check_ticker_status():
    """Check active/inactive ticker counts and show examples"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Count active tickers
    cursor.execute("SELECT COUNT(*) FROM scraper_tasks WHERE active = true")
    active_count = cursor.fetchone()[0]
    
    # Count inactive tickers
    cursor.execute("SELECT COUNT(*) FROM scraper_tasks WHERE active = false")
    inactive_count = cursor.fetchone()[0]
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM scraper_tasks")
    total_count = cursor.fetchone()[0]
    
    print(f"Ticker Status Summary:")
    print(f"Active (true): {active_count}")
    print(f"Inactive (false): {inactive_count}")
    print(f"Total: {total_count}")
    
    # Show some examples of each
    if active_count > 0:
        cursor.execute("SELECT symbol FROM scraper_tasks WHERE active = true LIMIT 5")
        active_examples = [row[0] for row in cursor.fetchall()]
        print(f"\nActive examples: {active_examples}")
    
    if inactive_count > 0:
        cursor.execute("SELECT symbol FROM scraper_tasks WHERE active = false LIMIT 5")
        inactive_examples = [row[0] for row in cursor.fetchall()]
        print(f"Inactive examples: {inactive_examples}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_ticker_status()