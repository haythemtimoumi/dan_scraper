#!/usr/bin/env python
"""
Script to delete stock data by date from the database
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def delete_data_by_date(date_str):
    """
    Delete all stock data for a specific date
    
    Args:
        date_str: Date in YYYY-MM-DD format
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate date format
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-01-15)")
        return False
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            connect_timeout=30
        )
        print(f"✅ Connected to database")
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return False

    cursor = conn.cursor()
    
    try:
        # Check how many records exist for this date
        cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = %s", (date_str,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"⚠️ No records found for date {date_str}")
            return True
        
        print(f"📊 Found {count} records for date {date_str}")
        
        # Confirm deletion
        confirm = input(f"❓ Are you sure you want to delete {count} records for {date_str}? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Deletion cancelled")
            return False
        
        # Delete records
        cursor.execute("DELETE FROM stock_analysis WHERE date = %s", (date_str,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        print(f"✅ Successfully deleted {deleted_count} records for date {date_str}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error deleting data: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

def list_available_dates():
    """List all available dates in the database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            connect_timeout=30
        )
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT date, COUNT(*) as record_count 
            FROM stock_analysis 
            GROUP BY date 
            ORDER BY date DESC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("📊 No data found in database")
            return
        
        print("\n📅 Available dates:")
        print("-" * 30)
        for date, count in results:
            print(f"{date}: {count} records")
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error listing dates: {e}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Delete stock data by date")
    parser.add_argument("--date", help="Date to delete (YYYY-MM-DD format)")
    parser.add_argument("--list", action="store_true", help="List available dates")
    
    args = parser.parse_args()
    
    if args.list:
        list_available_dates()
    elif args.date:
        delete_data_by_date(args.date)
    else:
        # Interactive mode
        print("🗑️ Stock Data Deletion Tool")
        print("=" * 30)
        
        # Show available dates first
        list_available_dates()
        
        # Get date from user
        date_input = input("\n📅 Enter date to delete (YYYY-MM-DD) or 'q' to quit: ")
        
        if date_input.lower() == 'q':
            print("👋 Goodbye!")
        else:
            delete_data_by_date(date_input)