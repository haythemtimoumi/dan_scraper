#!/usr/bin/env python
import requests
from merge_and_save import update_price_data

def fetch_prices_to_db(tickers):
    """Fetch prices and update database directly"""
    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Fetching {ticker}...")
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            response = requests.get(url)
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                update_price_data(ticker, f"${price}")
                print(f"Updated {ticker}: ${price}")
            else:
                print(f"No price found for {ticker}")
                
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    
    print(f"Completed price fetching for {len(tickers)} tickers")

if __name__ == "__main__":
    test_tickers = ['CF', 'OLN', 'INMD']
    fetch_prices_to_db(test_tickers)