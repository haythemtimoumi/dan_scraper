#!/usr/bin/env python3
"""
Database Restore from S3 Backup
Downloads backup files from S3 and restores to database
"""

import boto3
import pandas as pd
import psycopg2
import json
import os
import numpy as np
from datetime import datetime

# S3 Configuration
S3_CONFIG = {
    'bucket_name': 'dan-scraper-csv-files',
    'region': 'ca-central-1'
}

# Database Configuration (UPDATE FOR YOUR LOCAL PC)
DB_CONFIG = {
    'host': 'localhost',  # Change to your local database host
    'port': '5432', 
    'dbname': 'stocklist',  # Change to your local database name
    'user': 'haystockuser',  # Change to your local database user
    'password': 'zro=+)1*-D9X'  # Change to your local database password
}

def download_backup_from_s3():
    """Download latest backup files from S3"""
    print("📥 Downloading backup files from S3...")
    
    s3 = boto3.client('s3', region_name=S3_CONFIG['region'])
    bucket = S3_CONFIG['bucket_name']
    
    # List backup files
    response = s3.list_objects_v2(Bucket=bucket, Prefix='database_backup_')
    
    if 'Contents' not in response:
        print("❌ No backup files found in S3")
        return None, None
    
    # Find latest backup files
    json_file = None
    csv_file = None
    
    for obj in response['Contents']:
        key = obj['Key']
        if key.endswith('.json'):
            json_file = key
        elif key.endswith('.csv'):
            csv_file = key
    
    if not json_file or not csv_file:
        print("❌ Incomplete backup files in S3")
        return None, None
    
    # Download files
    print(f"📁 Downloading {json_file}...")
    s3.download_file(bucket, json_file, json_file)
    
    print(f"📁 Downloading {csv_file}...")
    s3.download_file(bucket, csv_file, csv_file)
    
    print("✅ Backup files downloaded successfully")
    return json_file, csv_file

def check_database_tables():
    """Check if all required tables exist"""
    print("🔍 Checking database tables...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    required_tables = ['comment', 'guru', 'guru_ticker_map', 'old_stock_analysis', 
                      'scraper_tasks', 'stock_analysis', 'users']
    
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    cursor.close()
    conn.close()
    
    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        print("Please create these tables in your database first")
        return False
    
    print("✅ All required tables exist")
    return True

def restore_from_json(json_file):
    """Restore complete database from JSON backup"""
    print(f"🔄 Restoring database from {json_file}...")
    
    with open(json_file, 'r') as f:
        backup = json.load(f)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear existing data
    tables = ['comment', 'guru', 'guru_ticker_map', 'old_stock_analysis', 
              'scraper_tasks', 'stock_analysis', 'users']
    
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        print(f"🗑️ Cleared {table}")
    
    # Restore data
    total_restored = 0
    for table_name, records in backup['data'].items():
        if records:
            print(f"📊 Restoring {table_name}...")
            
            for i, record in enumerate(records):
                try:
                    # Clean the record - handle nan, null, and data type issues
                    cleaned_record = {}
                    for key, value in record.items():
                        if pd.isna(value) or value == 'nan' or str(value).lower() == 'nan':
                            cleaned_record[key] = None
                        elif isinstance(value, float) and (value != value):  # Check for NaN
                            cleaned_record[key] = None
                        else:
                            cleaned_record[key] = value
                    
                    # Skip id column to let auto-increment handle it
                    if 'id' in cleaned_record:
                        del cleaned_record['id']
                    
                    columns = ', '.join(cleaned_record.keys())
                    placeholders = ', '.join(['%s'] * len(cleaned_record))
                    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    cursor.execute(sql, tuple(cleaned_record.values()))
                    
                except Exception as e:
                    print(f"❌ Error inserting into {table_name}:")
                    print(f"   Record {i+1}: {e}")
                    continue
            
            total_restored += len(records)
            print(f"✅ Restored {table_name}: {len(records)} records")
    
    # Reset sequences to avoid ID conflicts
    print("🔄 Resetting ID sequences...")
    for table in restore_order:
        try:
            cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
        except:
            pass  # Skip if table doesn't have id column
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"🎉 Database restore completed: {total_restored:,} total records")

def restore_from_csv(csv_file):
    """Restore main table from CSV backup (alternative method)"""
    print(f"🔄 Restoring main table from {csv_file}...")
    
    df = pd.read_csv(csv_file)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clear stock_analysis table
    cursor.execute("TRUNCATE TABLE stock_analysis RESTART IDENTITY CASCADE")
    
    # Insert CSV data
    for _, row in df.iterrows():
        columns = ', '.join(row.index)
        placeholders = ', '.join(['%s'] * len(row))
        sql = f"INSERT INTO stock_analysis ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, tuple(row.values))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Restored stock_analysis: {len(df)} records")

def main():
    """Main restore process"""
    print("🚀 Starting database restore from S3...")
    
    try:
        # Download backup files
        json_file, csv_file = download_backup_from_s3()
        if not json_file:
            return
        
        # Check tables exist
        if not check_database_tables():
            return
        
        # Choose restore method
        print("\nChoose restore method:")
        print("1. Complete restore from JSON (recommended)")
        print("2. Main table only from CSV")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == '1':
            restore_from_json(json_file)
        elif choice == '2':
            restore_from_csv(csv_file)
        else:
            print("Invalid choice")
            return
        
        print("\n🎉 Database restore completed successfully!")
        
    except Exception as e:
        print(f"❌ Restore failed: {e}")

if __name__ == "__main__":
    main()