#!/usr/bin/env python
"""
Quick script to check data count for a specific date
"""

import psycopg2
from config.settings import DB_CONFIG

def check_data_count(date_str='2025-07-25'):
    """Check how many records exist for a specific date"""
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            connect_timeout=30
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = %s", (date_str,))
        count = cursor.fetchone()[0]
        
        print(f"📊 Records for {date_str}: {count}")
        
        cursor.close()
        conn.close()
        return count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

if __name__ == "__main__":
    check_data_count('2025-07-25')