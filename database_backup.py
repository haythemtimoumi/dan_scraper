#!/usr/bin/env python3
"""
Complete Database Backup to CSV and S3
Creates database_backup_27_08_2025.csv with all tables
"""

import pandas as pd
import psycopg2
from datetime import datetime
from utils.s3_uploader import S3CSVUploader
import json

# Database connection from rules
DB_CONFIG = {
    'host': '162.248.101.75',
    'port': '5432', 
    'database': 'stocklist',
    'user': 'haystockuser',
    'password': 'zro=+)1*-D9X'
}

def backup_database():
    """Create complete database backup"""
    print("🗄️ Starting complete database backup...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Tables to backup
    tables = [
        'comment', 'guru', 'guru_ticker_map', 'old_stock_analysis',
        'scraper_tasks', 'stock_analysis', 'users'
    ]
    
    backup_data = {}
    total_records = 0
    
    for table in tables:
        print(f"📊 Backing up table: {table}")
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        backup_data[table] = df.to_dict('records')
        total_records += len(df)
        print(f"   ✅ {len(df):,} records backed up")
    
    conn.close()
    
    # Create backup metadata
    backup_info = {
        'backup_date': '2025-08-27',
        'total_tables': len(tables),
        'total_records': total_records,
        'tables': {table: len(backup_data[table]) for table in tables}
    }
    
    # Combine all data
    complete_backup = {
        'metadata': backup_info,
        'data': backup_data
    }
    
    # Save as JSON first (preserves structure)
    backup_filename = 'database_backup_27_08_2025.json'
    with open(backup_filename, 'w') as f:
        json.dump(complete_backup, f, indent=2, default=str)
    
    print(f"✅ JSON backup saved: {backup_filename}")
    
    # Also create CSV for main table (stock_analysis)
    main_df = pd.DataFrame(backup_data['stock_analysis'])
    csv_filename = 'database_backup_27_08_2025.csv'
    main_df.to_csv(csv_filename, index=False)
    print(f"✅ CSV backup saved: {csv_filename}")
    
    # Upload to S3
    uploader = S3CSVUploader()
    
    # Upload JSON backup
    with open(backup_filename, 'rb') as f:
        uploader.s3_client.put_object(
            Bucket=uploader.bucket_name,
            Key=backup_filename,
            Body=f.read(),
            ContentType='application/json'
        )
    print(f"✅ JSON backup uploaded to S3: {backup_filename}")
    
    # Upload CSV backup
    uploader.s3_client.put_object(
        Bucket=uploader.bucket_name,
        Key=csv_filename,
        Body=open(csv_filename, 'rb').read(),
        ContentType='text/csv'
    )
    print(f"✅ CSV backup uploaded to S3: {csv_filename}")
    
    print(f"\n🎉 Database backup complete!")
    print(f"📊 Total: {total_records:,} records from {len(tables)} tables")
    print(f"📁 Files: {backup_filename} (complete), {csv_filename} (main table)")
    
    return backup_filename, csv_filename

if __name__ == "__main__":
    backup_database()