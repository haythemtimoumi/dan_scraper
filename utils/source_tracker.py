"""
Module to track and manage data sources for stock data
"""

import os
import csv
from datetime import datetime

def save_ticker_source(ticker, source):
    """
    Save a ticker's source to a tracking file
    
    Args:
        ticker (str): The ticker symbol
        source (str): The source ('rule1' or 'manual')
    """
    os.makedirs('data', exist_ok=True)
    source_file = 'data/ticker_sources.csv'
    
    # Check if file exists and create with header if not
    if not os.path.exists(source_file):
        with open(source_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ticker', 'source', 'date_added'])
    
    # Read existing sources
    sources = {}
    with open(source_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sources[row['ticker']] = row
    
    # Update or add the ticker
    today = datetime.now().strftime('%Y-%m-%d')
    sources[ticker] = {'ticker': ticker, 'source': source, 'date_added': today}
    
    # Write back to file
    with open(source_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ticker', 'source', 'date_added'])
        writer.writeheader()
        writer.writerows(sources.values())

def save_tickers_source(tickers, source):
    """
    Save multiple tickers' source to the tracking file
    
    Args:
        tickers (list): List of ticker symbols
        source (str): The source ('rule1' or 'manual')
    """
    for ticker in tickers:
        save_ticker_source(ticker, source)

def get_ticker_source(ticker):
    """
    Get the source for a ticker
    
    Args:
        ticker (str): The ticker symbol
        
    Returns:
        str: The source ('rule1', 'manual', or 'unknown')
    """
    source_file = 'data/ticker_sources.csv'
    
    if not os.path.exists(source_file):
        return 'unknown'
    
    with open(source_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ticker'] == ticker:
                return row['source']
    
    return 'unknown'

def get_all_ticker_sources():
    """
    Get sources for all tracked tickers
    
    Returns:
        dict: Dictionary mapping tickers to their sources
    """
    source_file = 'data/ticker_sources.csv'
    sources = {}
    
    if not os.path.exists(source_file):
        return sources
    
    with open(source_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sources[row['ticker']] = row['source']
    
    return sources