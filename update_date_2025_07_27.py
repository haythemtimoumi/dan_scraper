#!/usr/bin/env python
# Script to update date from 2025-07-27 to 2025-07-26 in the database

import psycopg2
from config.settings import DB_CONFIG

def update_date_in_database():
    """
    Update all records with date 2025-07-27 to 2025-07-26
    """
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        cursor = conn.cursor()
        
        # First, check how many records have the date 2025-07-27
        cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = '2025-07-27'")
        count_before = cursor.fetchone()[0]
        print(f"📊 Found {count_before} records with date 2025-07-27")
        
        if count_before == 0:
            print("✅ No records found with date 2025-07-27")
            return True
        
        # Update the date from 2025-07-27 to 2025-07-26
        update_query = """
        UPDATE stock_analysis 
        SET date = '2025-07-26' 
        WHERE date = '2025-07-27'
        """
        
        cursor.execute(update_query)
        updated_count = cursor.rowcount
        
        # Commit the changes
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = '2025-07-26'")
        count_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = '2025-07-27'")
        remaining_count = cursor.fetchone()[0]
        
        print(f"✅ Successfully updated {updated_count} records")
        print(f"📊 Records with date 2025-07-26: {count_after}")
        print(f"📊 Records with date 2025-07-27 remaining: {remaining_count}")
        
        return True
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"❌ Error updating database: {e}")
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔄 Updating date from 2025-07-27 to 2025-07-26...")
    success = update_date_in_database()
    
    if success:
        print("✅ Date update completed successfully!")
    else:
        print("❌ Date update failed!")