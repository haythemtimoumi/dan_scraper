#!/usr/bin/env python3
"""
Daily CSV uploader to S3
Uploads ticker_data.csv and stockscores_data.csv with date suffix
"""

import pandas as pd
from datetime import datetime
from utils.s3_uploader import S3CSVUploader

def upload_daily_files():
    """Upload both CSV files to S3 with today's date"""
    uploader = S3CSVUploader()
    
    # Files to upload
    files_to_upload = [
        'ticker_data.csv',
        'stockscores_data.csv'
    ]
    
    uploaded_files = []
    
    for filename in files_to_upload:
        try:
            # Read the CSV file
            df = pd.read_csv(filename)
            
            # Get base name without extension
            base_name = filename.replace('.csv', '')
            
            # Upload to S3 with date suffix
            s3_key = uploader.save_csv_to_s3(df, base_name)
            
            if s3_key:
                uploaded_files.append(s3_key)
                print(f"✅ Uploaded {filename} as {s3_key}")
            else:
                print(f"❌ Failed to upload {filename}")
                
        except FileNotFoundError:
            print(f"⚠️ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error uploading {filename}: {e}")
    
    print(f"\n📊 Summary: {len(uploaded_files)} files uploaded successfully")
    return uploaded_files

if __name__ == "__main__":
    print("🚀 Starting daily CSV upload to S3...")
    uploaded = upload_daily_files()
    print("✅ Upload process completed!")