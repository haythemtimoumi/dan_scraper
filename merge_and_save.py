#!/usr/bin/env python
# Script to merge ticker_data.csv and stockscores_data.csv and save to database

import psycopg2
import os
from datetime import datetime
from config.settings import DB_CONFIG

def merge_and_save():
    """
    Merge ticker_data.csv and stockscores_data.csv and save to database
    """
    from utils.source_tracker import get_all_ticker_sources
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"🔄 Merging data and saving to database for {today}...")
    
    # Get source tracking data
    ticker_sources = get_all_ticker_sources()
    print(f"📊 Loaded {len(ticker_sources)} ticker sources")
    
    # Override with dan_portfolio_list source for current run
    dan_portfolio_sources = {}
    if os.path.exists('dan_portfolio_tickers.txt'):
        with open('dan_portfolio_tickers.txt', 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        ticker = parts[0].strip()
                        source = parts[1].strip()
                        dan_portfolio_sources[ticker] = source
        print(f"📋 Loaded {len(dan_portfolio_sources)} dan_portfolio sources")
    
    # Connect to the database with timeout
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            connect_timeout=30
        )
        print(f"✅ Connected to database at {DB_CONFIG['host']}")
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Try: Check VPS firewall, PostgreSQL config, or use localhost if running locally")
        return

    cursor = conn.cursor()
    
    # Check existing data for today
    cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE date = %s", (today,))
    existing_count = cursor.fetchone()[0]
    print(f"📊 Found {existing_count} existing records for today ({today}) - will update/insert as needed")
    
    # Read auto_prices.csv to get last_price data
    price_data = {}
    if os.path.exists('auto_prices.csv'):
        import pandas as pd
        price_df = pd.read_csv('auto_prices.csv')
        print(f"📊 Read {len(price_df)} price records from auto_prices.csv")
        
        for _, row in price_df.iterrows():
            ticker = row['ticker']
            last_price = row.get('last_price')
            if pd.notna(last_price) and last_price != '':
                price_data[ticker] = str(int(last_price))
    else:
        print("❌ auto_prices.csv not found")
    
    # Read ticker_data.csv using pandas to handle quoted values
    ticker_data = {}
    ticker_file = None
    for file in ['fresh_ticker_data.csv', 'ticker_data.csv']:
        if os.path.exists(file):
            ticker_file = file
            break
    
    if ticker_file:
        import pandas as pd
        df = pd.read_csv(ticker_file)
        print(f"📊 Read {len(df)} rows from {ticker_file}")
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            
            # Clean price values and handle decimal formatting
            buy_price_raw = str(row.get('buy_price', '')).replace('$', '').replace(',', '').replace('"', '')
            last_price_raw = str(row.get('last_price', '')).replace('$', '').replace(',', '').replace('"', '')
            
            # Keep original decimal values (don't convert to integer)
            try:
                buy_price_clean = str(float(buy_price_raw)) if buy_price_raw and buy_price_raw != '' and buy_price_raw != 'N/A' else ''
            except (ValueError, TypeError):
                buy_price_clean = buy_price_raw if buy_price_raw != 'N/A' else ''
                
            try:
                last_price_clean = str(float(last_price_raw)) if last_price_raw and last_price_raw != '' and last_price_raw != 'N/A' else ''
            except (ValueError, TypeError):
                last_price_clean = last_price_raw if last_price_raw != 'N/A' else ''
            
            # Use price from auto_prices.csv if available, otherwise from CSV
            final_last_price = price_data.get(ticker, last_price_clean)
            
            ticker_data[ticker] = {
                'rule1_score': row.get('rule1_score'),
                'management_score': row.get('management_score'),
                'moat_score': row.get('moat_score'),
                'buy_price': buy_price_clean,
                'last_price': final_last_price,
                'dividend': row.get('dividend', 'N/A'),
                'cash_per_share': row.get('cash_per_share', 'N/A'),
                'pbt': row.get('guru', 'N/A'),
                'last_gr': row.get('last_gr', 'N/A'),
                'long_gr': row.get('long_gr', 'N/A'),
                'full_name': row.get('full_name', 'N/A')
            }
    else:
        print("❌ ticker_data.csv not found")
    
    # Read stockscores_data.csv
    scores_data = {}
    scores_file = None
    for file in ['fresh_stockscores_data.csv', 'stockscores_data.csv']:
        if os.path.exists(file):
            scores_file = file
            break
    
    if scores_file:
        with open(scores_file, 'r') as f:
            scores_lines = f.readlines()
            print(f"📊 Read {len(scores_lines)} lines from {scores_file}")
            
            # Skip header
            header = True
            for line in scores_lines:
                if header:
                    header = False
                    continue
                
                parts = line.strip().split(',')
                if len(parts) >= 4:  # Date, Ticker, Signal Score, Sentiment Score
                    ticker = parts[1]
                    
                    # Handle N/A values for scores
                    signal_score = parts[2] if len(parts) > 2 and parts[2] != 'N/A' else None
                    sentiment_score = parts[3] if len(parts) > 3 and parts[3] != 'N/A' else None
                    
                    # Get screenshot URL (5th column)
                    screenshot_url = parts[4] if len(parts) > 4 and parts[4] != 'N/A' else None
                    
                    scores_data[ticker] = {
                        'signal_score': signal_score,
                        'sentiment_score': sentiment_score,
                        'screenshot_url': screenshot_url
                    }
    else:
        print("❌ stockscores_data.csv not found")
    
    # Merge data and insert into database
    success_count = 0
    all_tickers = set(list(ticker_data.keys()) + list(scores_data.keys()))
    
    for ticker in all_tickers:
        try:
            # Get data from both sources
            ticker_info = ticker_data.get(ticker, {})
            scores_info = scores_data.get(ticker, {})
            
            # Prepare data for database
            rule1_score = ticker_info.get('rule1_score')
            if rule1_score == 'N/A' or rule1_score == '':
                rule1_score = None
            
            management_score = ticker_info.get('management_score')
            if management_score == 'N/A' or management_score == '':
                management_score = None
                
            moat_score = ticker_info.get('moat_score')
            if moat_score == 'N/A' or moat_score == '':
                moat_score = None
                
            buy_price = ticker_info.get('buy_price')
            if buy_price == 'N/A' or buy_price == '':
                buy_price = None
                
            last_price = ticker_info.get('last_price')
            if last_price == 'N/A' or last_price == '':
                last_price = None
            
            # Skip upside calculation for invalid buy_price values
            percentage_upside = None
            if buy_price and last_price:
                try:
                    buy_price_float = float(buy_price) if buy_price != '' else 0
                    last_price_float = float(last_price) if last_price != '' else 0
                    
                    # Skip calculation if buy_price is unreasonably high (likely data error)
                    if buy_price_float > 10000 or last_price_float <= 0:
                        percentage_upside = None
                    else:
                        percentage_upside = ((2 * buy_price_float - last_price_float) / last_price_float) * 100
                        percentage_upside = f"{percentage_upside:.2f}"
                except (ValueError, ZeroDivisionError):
                    percentage_upside = None
            
            # Handle N/A values and convert to integers if possible
            signal_score = scores_info.get('signal_score')
            if signal_score == 'N/A' or signal_score == '':  
                signal_score = None
            elif signal_score is not None:
                try:
                    signal_score = int(signal_score)
                except ValueError:
                    signal_score = None
                    
            sentiment_score = scores_info.get('sentiment_score')
            if sentiment_score == 'N/A' or sentiment_score == '':
                sentiment_score = None
            elif sentiment_score is not None:
                try:
                    sentiment_score = int(sentiment_score)
                except ValueError:
                    sentiment_score = None
                    
            # Get screenshot URL
            screenshot_url = scores_info.get('screenshot_url')
            if screenshot_url == 'N/A' or screenshot_url == '':
                screenshot_url = None
            
            # Get dividend and cash_per_share
            dividend = ticker_info.get('dividend')
            if dividend == 'N/A' or dividend == '':
                dividend = None
            
            cash_per_share = ticker_info.get('cash_per_share')
            if cash_per_share == 'N/A' or cash_per_share == '':
                cash_per_share = None
            
            # Get pbt (PBT at Current Price)
            pbt = ticker_info.get('pbt')
            if pbt == 'N/A' or pbt == '':
                pbt = None
            
            # Get growth rates
            last_gr = ticker_info.get('last_gr')
            if last_gr == 'N/A' or last_gr == '':
                last_gr = None
                
            long_gr = ticker_info.get('long_gr')
            if long_gr == 'N/A' or long_gr == '':
                long_gr = None
                
            # Get full name
            full_name = ticker_info.get('full_name')
            if full_name == 'N/A' or full_name == '':
                full_name = None
            
            # Get source for this ticker (prioritize dan_portfolio_list)
            source = dan_portfolio_sources.get(ticker, ticker_sources.get(ticker, 'unknown'))
            
            # Check if record exists first
            cursor.execute("""
                SELECT id FROM stock_analysis 
                WHERE date = %s AND ticker = %s AND source = %s
            """, (today, ticker, source))
            
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Skip existing record - don't update or delete
                print(f"⏭️ Skipping {ticker} ({source}) - already exists for {today}")
                continue
            else:
                # Insert new record only
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        date, ticker, source, rule1_score, management_score, moat_score,
                        buy_price, last_price, signal_score, sentiment_score, screenshot,
                        pbt, dividend, cash_per_share, per_upside, last_gr, long_gr, full_name
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    today, ticker, source, rule1_score, management_score, moat_score,
                    buy_price, last_price, signal_score, sentiment_score, screenshot_url,
                    pbt, dividend, cash_per_share, percentage_upside, last_gr, long_gr, full_name
                ))
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            conn.rollback()  # Rollback the transaction on error
            continue
    
    # Commit changes
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Successfully processed {success_count}/{len(all_tickers)} records (inserted only - existing records preserved) to database")
    return success_count

if __name__ == "__main__":
    merge_and_save()