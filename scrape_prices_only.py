#!/usr/bin/env python
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG

def scrape_prices_only():
    """Scrape prices for all active tickers and update last_price_scraped_at"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true")
    active_tickers = cursor.fetchall()
    
    if not active_tickers:
        print("❌ No active tickers found")
        return 0
    
    print(f"🎯 Price scraping for {len(active_tickers)} tickers")
    
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    success_count = 0
    
    for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(active_tickers, 1):
        print(f"\n💰 [{i}/{len(active_tickers)}] Price scraping {symbol}...")
        
        try:
            price = fetch_price(symbol)
            
            if price:
                # Save to stock_analysis
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source, last_price,
                        last_action, per_portfolio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (ticker_id, guru_id, current_timestamp, symbol, list_type, price, last_action, per_portfolio))
                
                # Update last_price_scraped_at timestamp
                cursor.execute("""
                    UPDATE scraper_tasks 
                    SET last_price_scraped_at = %s 
                    WHERE id = %s
                """, (now, ticker_id))
                
                success_count += 1
                print(f"✅ Price saved for {symbol}: ${price}")
            else:
                print(f"⚠️ Price fetch failed for {symbol}")
                
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n🎉 Price scraping complete: {success_count}/{len(active_tickers)} successful")
    return success_count

def fetch_price(ticker):
    """Fetch current price from Yahoo Finance"""
    try:
        import requests
        
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if response is successful
        if response.status_code != 200:
            print(f"⚠️ HTTP {response.status_code} for {ticker}")
            return None
            
        # Check if response has content
        if not response.text.strip():
            print(f"⚠️ Empty response for {ticker}")
            return None
            
        # Try to parse JSON
        try:
            data = response.json()
        except ValueError as json_error:
            print(f"⚠️ JSON parse error for {ticker}: {json_error}")
            print(f"Response content: {response.text[:200]}...")
            return None
            
        # Validate data structure
        if not data or 'chart' not in data:
            print(f"⚠️ Invalid data structure for {ticker}")
            return None
            
        if not data['chart']['result']:
            print(f"⚠️ No chart results for {ticker}")
            return None
            
        result = data['chart']['result'][0]
        if 'meta' not in result or 'regularMarketPrice' not in result['meta']:
            print(f"⚠️ Missing price data for {ticker}")
            return None
            
        price = result['meta']['regularMarketPrice']
        if price is None:
            print(f"⚠️ Null price for {ticker}")
            return None
            
        return round(float(price), 2)
        
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout fetching price for {ticker}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request error for {ticker}: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error for {ticker}: {e}")
    
    return None

if __name__ == "__main__":
    scrape_prices_only()