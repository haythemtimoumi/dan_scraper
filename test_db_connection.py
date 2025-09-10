#!/usr/bin/env python
import psycopg2
from config.settings import DB_CONFIG

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM scraper_tasks WHERE active = true")
    count = cursor.fetchone()[0]
    print(f"Active tickers found: {count}")
    
    cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true LIMIT 5")
    results = cursor.fetchall()
    print("Sample active tickers:")
    for row in results:
        print(f"  {row}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Database connection error: {e}")