#!/usr/bin/env python
import psycopg2
from config.settings import DB_CONFIG

def debug_database_connection():
    """Debug database connection and active tickers"""
    try:
        print("🔍 Testing database connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check total tickers
        cursor.execute("SELECT COUNT(*) FROM scraper_tasks")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total tickers in scraper_tasks: {total_count}")
        
        # Check active tickers
        cursor.execute("SELECT COUNT(*) FROM scraper_tasks WHERE active = true")
        active_count = cursor.fetchone()[0]
        print(f"✅ Active tickers: {active_count}")
        
        # Show first 10 active tickers
        cursor.execute("SELECT id, symbol, guru_id, list_type FROM scraper_tasks WHERE active = true LIMIT 10")
        sample_tickers = cursor.fetchall()
        
        print(f"\n📋 Sample active tickers:")
        for ticker_id, symbol, guru_id, list_type in sample_tickers:
            print(f"  - {symbol} (ID: {ticker_id}, Guru: {guru_id}, Type: {list_type})")
        
        cursor.close()
        conn.close()
        print(f"\n✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    debug_database_connection()