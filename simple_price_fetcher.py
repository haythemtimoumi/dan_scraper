import requests
import csv
import time
import json
import gspread
from google.oauth2.service_account import Credentials

def get_stock_price(ticker):
    """Get stock price with retry and multiple sources"""
    # Try Yahoo Finance first
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if 'chart' in data and data['chart']['result']:
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return int(price)
    except:
        pass
    
    # Try alternative Yahoo endpoint
    try:
        url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=price"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if 'quoteSummary' in data and data['quoteSummary']['result']:
            price = data['quoteSummary']['result'][0]['price']['regularMarketPrice']['raw']
            return int(price)
    except:
        pass
    
    return None

def fetch_all_prices():
    """Fetch prices for all tickers from combined_tickers.txt or fresh_combined_tickers.txt"""
    ticker_files = ['fresh_combined_tickers.txt', 'combined_tickers.txt']
    tickers = []
    
    for file in ticker_files:
        try:
            with open(file, 'r') as f:
                tickers = [line.strip() for line in f if line.strip()]
            break
        except FileNotFoundError:
            continue
    
    if not tickers:
        print("Error: combined_tickers.txt not found")
        return False
    
    print(f"Fetching prices for {len(tickers)} tickers...")
    
    results = []
    successful = 0
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Fetching {ticker}...", end=' ')
        
        price = get_stock_price(ticker)
        if price:
            results.append([ticker, price])
            print(f"${price}")
            successful += 1
        else:
            # Retry once more with delay
            time.sleep(2)
            price = get_stock_price(ticker)
            if price:
                results.append([ticker, price])
                print(f"${price} (retry)")
                successful += 1
            else:
                results.append([ticker, None])
                print("Failed")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Save to CSV
    with open('auto_prices.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ticker', 'last_price'])
        writer.writerows(results)
    
    # Save to Google Sheets
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key("1BcxCNDItk6nrYW5EwUm2h6Z8CnCsi4r5SJuC1LavYes")
        worksheet = sheet.sheet1
        worksheet.clear()
        
        # Upload header and data with formulas
        header = [['ticker', 'last_price', 'googlefinance_formula']]
        data_with_formulas = []
        
        for ticker, price in results:
            formula = f'=GOOGLEFINANCE("{ticker}","price")'
            data_with_formulas.append([ticker, price, formula])
        
        all_data = header + data_with_formulas
        worksheet.update(values=all_data, range_name=f'A1:C{len(all_data)}')
        
        print(f"\nCompleted: {successful}/{len(tickers)} prices fetched")
        print("Saved to auto_prices.csv")
        print(f"Uploaded to Google Sheets with formulas: {sheet.url}")
        return True
    except Exception as e:
        print(f"\nCompleted: {successful}/{len(tickers)} prices fetched")
        print("Saved to auto_prices.csv")
        print(f"Google Sheets upload failed: {e}")
        return True  # Still successful even if Google Sheets fails

if __name__ == "__main__":
    fetch_all_prices()