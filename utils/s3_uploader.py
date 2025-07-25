import boto3
import pandas as pd
from datetime import datetime
import os
from config.settings import S3_CONFIG

class S3CSVUploader:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=S3_CONFIG['region'])
        self.bucket_name = S3_CONFIG['bucket_name']
    
    def save_csv_to_s3(self, data, base_filename):
        """
        Save CSV data to S3 with date suffix
        
        Args:
            data: DataFrame or list of dictionaries
            base_filename: Base name for the file (e.g., 'ticker_data')
        
        Returns:
            str: S3 key of uploaded file
        """
        # Convert data to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Generate filename with date
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{base_filename}_{date_str}.csv"
        
        # Convert DataFrame to CSV string
        csv_buffer = df.to_csv(index=False)
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=csv_buffer,
                ContentType='text/csv'
            )
            print(f"✅ CSV uploaded to S3: s3://{self.bucket_name}/{filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to upload to S3: {e}")
            return None
    
    def save_local_and_s3(self, data, base_filename):
        """
        Save CSV both locally and to S3
        
        Args:
            data: DataFrame or list of dictionaries
            base_filename: Base name for the file
        
        Returns:
            tuple: (local_path, s3_key)
        """
        # Convert data to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Generate filename with date
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{base_filename}_{date_str}.csv"
        
        # Save locally
        local_path = filename
        df.to_csv(local_path, index=False)
        print(f"✅ CSV saved locally: {local_path}")
        
        # Upload to S3
        s3_key = self.save_csv_to_s3(df, base_filename)
        
        return local_path, s3_key

# Usage example
def upload_ticker_data(data):
    """Helper function to upload ticker data"""
    uploader = S3CSVUploader()
    return uploader.save_local_and_s3(data, 'ticker_data')

def upload_scores_data(data):
    """Helper function to upload scores data"""
    uploader = S3CSVUploader()
    return uploader.save_local_and_s3(data, 'scores_data')