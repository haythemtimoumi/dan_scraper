#!/usr/bin/env python
"""
Script to update date field in database records
"""

import psycopg2
from config.settings import DB_CONFIG

def update_date(old_date, new_date):
    """Update date field from old_date to new_date"""
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
        
        # Check current count
        cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = %s", (old_date,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"⚠️ No records found for date {old_date}")
            return
        
        print(f"📊 Found {count} records with date {old_date}")
        
        # Update the date
        cursor.execute("UPDATE stock_analysis SET date = %s WHERE date = %s", (new_date, old_date))
        updated_count = cursor.rowcount
        
        conn.commit()
        print(f"✅ Successfully updated {updated_count} records from {old_date} to {new_date}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_date('2025-07-26', '2025-07-25')