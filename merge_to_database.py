#!/usr/bin/env python
# Script to merge ticker_data.csv and stockscores_data.csv and save to database
#
# Database column mapping:
# - sticker_price → buy_price column
# - last_price → current_ratio column
# - percentage_upside → pe column

import pandas as pd
import os
from datetime import datetime
from utils.db_utils import save_stock_data_to_db
from utils.source_tracker import get_ticker_source, get_all_ticker_sources

def merge_and_save_to_db(save_csv_backup=True):
    """
    Merge ticker_data.csv and stockscores_data.csv based on ticker symbol
    and save directly to the database.
    
    Args:
        save_csv_backup (bool): Whether to also save a CSV backup
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("🔄 Merging data and saving to database...")
    
    try:
        # Check if files exist
        if not os.path.exists('ticker_data.csv'):
            print("❌ ticker_data.csv not found")
            return False
        
        if not os.path.exists('stockscores_data.csv'):
            print("❌ stockscores_data.csv not found")
            return False
        
        # Read the ticker data CSV with custom processing
        with open('ticker_data.csv', 'r') as f:
            lines = f.readlines()
        
        # Read the ticker data CSV directly with pandas
        # This will preserve all columns including Screenshot
        ticker_data = pd.read_csv('ticker_data.csv')
        
        # Ensure we have the core columns we need
        required_columns = [
            'ticker', 'rule1_score', 'management_score', 'moat_score', 
            'buy_price', 'last_price', 'percentage_upside'
        ]
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in ticker_data.columns]
        if missing_columns:
            print(f"⚠️ Missing columns in ticker_data.csv: {missing_columns}")
            # Create missing columns with default values
            for col in missing_columns:
                ticker_data[col] = None
        
        # Remove duplicate tickers, keeping the most recent entry
        ticker_data = ticker_data.drop_duplicates(subset=['ticker'], keep='last')
        
        # Read the stockscores data CSV
        stockscores_data = pd.read_csv('stockscores_data.csv')
        
        # Rename columns to match expected format
        stockscores_data = stockscores_data.rename(columns={
            'Ticker': 'ticker',
            'Signal Score': 'signal_score',
            'Sentiment Score': 'sentiment_score',
            'Screenshot': 'screenshot'
        })
        
        # Add today's date to both dataframes if not present
        today = datetime.now().strftime('%Y-%m-%d')
        if 'Date' not in ticker_data.columns:
            ticker_data['Date'] = today
        if 'Date' not in stockscores_data.columns:
            stockscores_data['Date'] = today
        
        # Get all ticker sources
        ticker_sources = get_all_ticker_sources()
        
        # Merge the dataframes on ticker column
        merged_data = pd.merge(ticker_data, stockscores_data, on='ticker', how='left')
        
        # Use Date from stockscores_data if available, otherwise use the one from ticker_data
        if 'Date_x' in merged_data.columns and 'Date_y' in merged_data.columns:
            merged_data['Date'] = merged_data['Date_y'].fillna(merged_data['Date_x'])
            merged_data = merged_data.drop(['Date_x', 'Date_y'], axis=1)
        
        # Ensure signal_score and sentiment_score columns exist
        if 'signal_score' not in merged_data.columns:
            merged_data['signal_score'] = None
        if 'sentiment_score' not in merged_data.columns:
            merged_data['sentiment_score'] = None
        if 'screenshot' not in merged_data.columns:
            merged_data['screenshot'] = None
        
        # Group data by source
        rule1_tickers = []
        manual_tickers = []
        
        for _, row in merged_data.iterrows():
            ticker = row['ticker']
            source = ticker_sources.get(ticker, 'unknown')
            
            if source == 'rule1':
                rule1_tickers.append(ticker)
            else:
                manual_tickers.append(ticker)
        
        # Save rule1 tickers
        if rule1_tickers:
            rule1_data = merged_data[merged_data['ticker'].isin(rule1_tickers)]
            print(f"📊 Saving {len(rule1_data)} tickers with source='rule1'")
            save_stock_data_to_db(rule1_data, source='rule1')
        
        # Save manual tickers
        if manual_tickers:
            manual_data = merged_data[merged_data['ticker'].isin(manual_tickers)]
            print(f"📊 Saving {len(manual_data)} tickers with source='manual'")
            save_stock_data_to_db(manual_data, source='manual')
        
        # Also save any tickers in stockscores_data that aren't in ticker_data
        extra_tickers = stockscores_data[~stockscores_data['ticker'].isin(ticker_data['ticker'])]
        if not extra_tickers.empty:
            print(f"📊 Found {len(extra_tickers)} additional tickers in stockscores_data")
            
            # Group by source
            extra_rule1 = []
            extra_manual = []
            
            for _, row in extra_tickers.iterrows():
                ticker = row['ticker']
                source = ticker_sources.get(ticker, 'manual')  # Default to manual if unknown
                
                if source == 'rule1':
                    extra_rule1.append(ticker)
                else:
                    extra_manual.append(ticker)
            
            # Save extra rule1 tickers
            if extra_rule1:
                extra_rule1_data = extra_tickers[extra_tickers['ticker'].isin(extra_rule1)]
                print(f"📊 Saving {len(extra_rule1_data)} additional tickers with source='rule1'")
                save_stock_data_to_db(extra_rule1_data, source='rule1')
            
            # Save extra manual tickers
            if extra_manual:
                extra_manual_data = extra_tickers[extra_tickers['ticker'].isin(extra_manual)]
                print(f"📊 Saving {len(extra_manual_data)} additional tickers with source='manual'")
                save_stock_data_to_db(extra_manual_data, source='manual')
        
        # Optionally save a CSV backup
        if save_csv_backup:
            merged_data.to_csv('merged_stock_data.csv', index=False)
            print(f"✅ Also saved backup to merged_stock_data.csv")
        
        print(f"✅ Total records processed: {len(merged_data)}")
        print(f"✅ Records with stockscores data: {merged_data['Signal Score'].notna().sum() if 'Signal Score' in merged_data.columns else 0}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error merging and saving data: {e}")
        return False

if __name__ == "__main__":
    merge_and_save_to_db()