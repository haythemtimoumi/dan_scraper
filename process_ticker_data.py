#!/usr/bin/env python
# Process ticker data from tab-separated format

import csv
import os
import sys
from custom_ticker_scraper import run_custom_scraper

def parse_ticker_data(data_text):
    """Parse tab-separated ticker data"""
    ticker_data = []
    lines = data_text.strip().split('\n')
    
    for line in lines:
        if line.strip():
            parts = line.split('\t')
            if parts:
                ticker = parts[0].strip()
                source = parts[1].strip() if len(parts) > 1 else 'dan_portfolio_list'
                if ticker:
                    ticker_data.append({'ticker': ticker, 'source': source})
    
    return ticker_data

def create_ticker_file(ticker_data, filename="input_tickers.csv"):
    """Create CSV file with ticker symbols and sources"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'source'])
        for item in ticker_data:
            writer.writerow([item['ticker'], item['source']])
    
    print(f"✅ Created {filename} with {len(ticker_data)} tickers")
    return filename

def clean_files():
    """Remove existing CSV and output files"""
    files_to_clean = [
        'input_tickers.csv',
        'fresh_ticker_data.csv',
        'custom_ticker_data.csv',
        'new_ticker_data.csv',
        'test_ticker_data.csv'
    ]
    
    cleaned_count = 0
    for file in files_to_clean:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  Removed {file}")
            cleaned_count += 1
    
    if cleaned_count == 0:
        print("✅ No files to clean")
    else:
        print(f"✅ Cleaned {cleaned_count} files")

if __name__ == "__main__":
    # Clean existing files first
    print("🧹 Cleaning existing files...")
    clean_files()
    print()
    
    # Read from text file
    try:
        with open('dan_portfolio_tickers.txt', 'r') as f:
            data = f.read()
        print(f"📄 Read ticker data from dan_portfolio_tickers.txt")
    except FileNotFoundError:
        print("❌ dan_portfolio_tickers.txt not found")
        sys.exit(1)
    
    # Parse tickers with sources
    ticker_data = parse_ticker_data(data)
    tickers = [item['ticker'] for item in ticker_data]
    print(f"📋 Parsed {len(ticker_data)} tickers: {tickers}")
    
    # Create ticker file
    ticker_file = create_ticker_file(ticker_data)
    
    # Run custom scraper
    print("\n🚀 Starting custom scraper...")
    success = run_custom_scraper(ticker_file, "fresh_ticker_data.csv")
    
    sys.exit(0 if success else 1)