#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def scrape_active_tickers():
    """Get active tickers from scraper_tasks and scrape data to stock_analysis"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get active tickers
    cursor.execute("SELECT id, symbol, guru_id, list_type FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("No active tickers found")
        return
    
    tickers = [row[1] for row in active_tickers]
    print(f"Scraping {len(tickers)} active tickers: {tickers}")
    
    # Scrape and save data
    from merge_and_save import merge_and_save
    merge_and_save()
    
    # Send Firebase notification
    from firebase_notifier import FirebaseNotifier
    FirebaseNotifier.send_notification(
        title="Scraper Complete",
        body=f"Process ticker data finished: {len(tickers)} tickers processed",
        data={"script": "process_ticker_data", "ticker_count": str(len(tickers)), "timestamp": str(datetime.now())}
    )
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    scrape_active_tickers()