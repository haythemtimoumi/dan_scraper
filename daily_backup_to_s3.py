#!/usr/bin/env python3
"""
Daily Database Backup to S3
Replaces existing backup with latest complete database
"""

import pandas as pd
import psycopg2
from datetime import datetime
from utils.s3_uploader import S3CSVUploader
import json
import boto3
from config.settings import S3_CONFIG

# Database connection from rules
DB_CONFIG = {
    'host': '162.248.101.75',
    'port': '5432', 
    'database': 'stocklist',
    'user': 'haystockuser',
    'password': 'zro=+)1*-D9X'
}

def daily_backup_to_s3():
    """Create fresh complete database backup and replace in S3"""
    current_date = datetime.now().strftime('%d_%m_%Y')
    print(f"🗄️ Creating daily database backup for {current_date}...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Tables to backup
    tables = [
        'comment', 'guru', 'guru_ticker_map', 'old_stock_analysis',
        'scraper_tasks', 'stock_analysis', 'users'
    ]
    
    backup_data = {}
    total_records = 0
    
    for table in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        backup_data[table] = df.to_dict('records')
        total_records += len(df)
    
    conn.close()
    
    # Create backup metadata
    backup_info = {
        'backup_date': datetime.now().strftime('%Y-%m-%d'),
        'total_tables': len(tables),
        'total_records': total_records,
        'tables': {table: len(backup_data[table]) for table in tables}
    }
    
    # Combine all data
    complete_backup = {
        'metadata': backup_info,
        'data': backup_data
    }
    
    # Fixed filenames (always same name)
    json_filename = f'database_backup_{current_date}.json'
    csv_filename = f'database_backup_{current_date}.csv'
    
    # Save JSON locally
    with open(json_filename, 'w') as f:
        json.dump(complete_backup, f, indent=2, default=str)
    
    # Save CSV locally (main table)
    main_df = pd.DataFrame(backup_data['stock_analysis'])
    main_df.to_csv(csv_filename, index=False)
    
    # Upload to S3 (replace existing)
    s3 = boto3.client('s3', region_name=S3_CONFIG['region'])
    bucket = S3_CONFIG['bucket_name']
    
    # Delete old backups first
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix='database_backup_')
        if 'Contents' in response:
            old_files = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(Bucket=bucket, Delete={'Objects': old_files})
            print(f"🗑️ Deleted {len(old_files)} old backup files")
    except Exception as e:
        print(f"⚠️ Could not delete old files: {e}")
    
    # Upload new backups
    with open(json_filename, 'rb') as f:
        s3.put_object(Bucket=bucket, Key=json_filename, Body=f.read(), ContentType='application/json')
    
    with open(csv_filename, 'rb') as f:
        s3.put_object(Bucket=bucket, Key=csv_filename, Body=f.read(), ContentType='text/csv')
    
    print(f"✅ Fresh backup uploaded to S3:")
    print(f"   📁 {json_filename} (complete database)")
    print(f"   📁 {csv_filename} (main table)")
    print(f"📊 Total: {total_records:,} records from {len(tables)} tables")
    
    return json_filename, csv_filename

if __name__ == "__main__":
    daily_backup_to_s3()