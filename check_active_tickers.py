#!/usr/bin/env python
import psycopg2
from config.settings import DB_CONFIG

def check_active_tickers():
    """Check what active tickers are in the database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, guru_id, list_type FROM scraper_tasks WHERE active = true ORDER BY symbol")
    active_tickers = cursor.fetchall()
    
    print(f"Found {len(active_tickers)} active tickers:")
    for ticker_id, symbol, guru_id, list_type in active_tickers:
        print(f"  - {symbol} (ID: {ticker_id}, Guru ID: {guru_id}, Type: {list_type})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_active_tickers()