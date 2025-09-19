import os
import psycopg2
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def get_active_tickers():
    conn = psycopg2.connect(
        host='162.248.101.75',
        port='5432',
        dbname='stocklist',
        user='haystockuser',
        password='zro=+)1*-D9X'
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, symbol, guru_id, list_type, last_action, per_portfolio, stock_ticker 
        FROM scraper_tasks 
        WHERE active = true
        ORDER BY 
            CASE WHEN stock_ticker IS NOT NULL AND stock_ticker != '' AND stock_ticker != symbol THEN 0 ELSE 1 END,
            symbol
    """)
    tickers = cursor.fetchall()
    cursor.close()
    conn.close()
    return tickers

def get_rule1_data(ticker):
    # This function should return Rule1 data - placeholder for now
    return {}

def fetch_yahoo_price(ticker):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    price = result['meta']['regularMarketPrice']
                    if price:
                        price_rounded = round(float(price), 2)
                        print(f"    Yahoo price found for {ticker}: ${price_rounded}")
                        return price_rounded
        print(f"    No Yahoo price found for {ticker}")
    except Exception as e:
        print(f"    Error fetching Yahoo price for {ticker}: {e}")
    return None 

def login_stockscores(driver):
    driver.get("https://www.stockscores.com/my-account/")
    
    # Check if already logged in
    if "login" not in driver.current_url.lower():
        print("Already logged in")
        return
    
    try:
        email_field = driver.find_element(By.ID, "login-form-username")
        email_field.send_keys(os.getenv('STOCKSCORES_EMAIL'))
        
        password_field = driver.find_element(By.ID, "login-form-password")
        password_field.send_keys(os.getenv('STOCKSCORES_PASSWORD'))
        
        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()
    except:
        print("Login elements not found - may already be logged in")

def scrape_ticker_data(driver, ticker):
    url = f"https://www.stockscores.com/charts/charts/?ticker={ticker}"
    driver.get(url)
    
    # Get Rule1 data
    rule1_data = get_rule1_data(ticker)
    
    # Get Yahoo price
    yahoo_price = fetch_yahoo_price(ticker)
    
    try:
        # Wait max 3 seconds for elements to load
        score_elements = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[@style='font-size:24px;']/b"))
        )
        
        sentiment_score = score_elements[0].text if len(score_elements) > 0 else ""
        signal_score = score_elements[1].text if len(score_elements) > 1 else ""
        
        # Get chart image URL
        chart_img = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.changeWidth"))
        )
        chart_url = chart_img.get_attribute("src")
        
        # Calculate upside percentage
        per_upside = None
        if rule1_data.get('buy_price') and yahoo_price and yahoo_price > 0:
            try:
                buy_price_num = float(rule1_data['buy_price'])
                per_upside = round((2 * buy_price_num - yahoo_price) / yahoo_price * 100, 2)
            except (ValueError, TypeError):
                per_upside = None
        
        print(f"{ticker}: Rule1={rule1_data.get('rule1_score')}, Signal={signal_score}, Price=${yahoo_price}, Upside={per_upside}%")
        
        # Ensure all Rule1 columns are present
        default_rule1 = {
            'rule1_score': None, 'moat_score': None, 'management_score': None,
            'buy_price': None, 'full_name': None, 'last_gr': None, 'long_gr': None, 'pbt': None
        }
        default_rule1.update(rule1_data)
        
        return {
            'ticker': ticker,
            'sentiment_score': sentiment_score,
            'signal_score': signal_score,
            'chart_url': chart_url,
            'yahoo_price': yahoo_price,
            'per_upside': per_upside,
            **default_rule1
        }
    except Exception as e:
        print(f"Timeout/Error scraping {ticker}: skipping")
        # Still return Rule1 and Yahoo data even if StockScores fails
        # Ensure all Rule1 columns are present
        default_rule1 = {
            'rule1_score': None, 'moat_score': None, 'management_score': None,
            'buy_price': None, 'full_name': None, 'last_gr': None, 'long_gr': None, 'pbt': None
        }
        default_rule1.update(rule1_data)
        
        return {
            'ticker': ticker,
            'sentiment_score': None,
            'signal_score': None,
            'chart_url': None,
            'yahoo_price': yahoo_price,
            'per_upside': None,
            **default_rule1
        }

def main():
    tickers = get_active_tickers()
    
    # Process all active tickers
    print(f"Processing all {len(tickers)} active tickers")
    
    # Database connection
    conn = psycopg2.connect(
        host='162.248.101.75',
        port='5432',
        dbname='stocklist',
        user='haystockuser',
        password='zro=+)1*-D9X'
    )
    cursor = conn.cursor()
    
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome_test')
    driver = webdriver.Chrome(options=chrome_options)
    success_count = 0
    
    try:
        login_stockscores(driver)
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio, stock_ticker) in enumerate(tickers, 1):
            try:
                # Check if we have different tickers to scrape
                has_stock_ticker = stock_ticker and stock_ticker.strip() and stock_ticker != symbol
                tickers_to_scrape = [symbol]
                if has_stock_ticker:
                    tickers_to_scrape.append(stock_ticker)
                
                print(f"\n[{i}/{len(tickers)}] Processing {symbol}...")
                if has_stock_ticker:
                    print(f"    Will scrape both: {symbol} and {stock_ticker}")
                
                # Get Rule1 data from database (use original symbol for database lookup)
                cursor.execute("""
                    SELECT rule1_score, moat_score, management_score, buy_price, 
                           full_name, last_gr, long_gr, pbt
                    FROM stock_analysis 
                    WHERE ticker = %s AND rule1_score IS NOT NULL
                    AND date >= date_trunc('month', CURRENT_DATE)
                    ORDER BY date DESC LIMIT 1
                """, (symbol,))
                
                rule1_data = cursor.fetchone()
                if rule1_data:
                    rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = rule1_data
                    print(f"    Rule1 data found for {symbol}")
                else:
                    rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = (None, None, None, None, None, None, None, None)
                    print(f"    No Rule1 data found for {symbol} this month")
                
                # Scrape data for each ticker separately and save individual records
                for ticker_to_scrape in tickers_to_scrape:
                    print(f"    Scraping {ticker_to_scrape}...")
                    
                    # Get StockScores data for this specific ticker
                    data = scrape_ticker_data(driver, ticker_to_scrape)
                    if data:
                        sentiment_score = data.get('sentiment_score')
                        signal_score = data.get('signal_score')
                        chart_url = data.get('chart_url')
                    else:
                        sentiment_score = signal_score = chart_url = None
                    
                    # Get Yahoo price for this specific ticker
                    yahoo_price = fetch_yahoo_price(ticker_to_scrape)
                    
                    # Calculate upside
                    per_upside = None
                    if buy_price and yahoo_price and yahoo_price > 0:
                        try:
                            buy_price_num = float(buy_price)
                            per_upside = round((2 * buy_price_num - yahoo_price) / yahoo_price * 100, 2)
                        except (ValueError, TypeError):
                            per_upside = None
                    
                    # Insert separate record for this ticker
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                        INSERT INTO stock_analysis (
                            ticker_id, guru_id, date, ticker, source,
                            rule1_score, moat_score, management_score, buy_price,
                            full_name, last_gr, long_gr, pbt,
                            signal_score, sentiment_score, screenshot,
                            last_price, last_action, per_portfolio, per_upside
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ticker_id, guru_id, current_time, ticker_to_scrape, list_type,
                        rule1_score, moat_score, management_score, buy_price,
                        full_name, last_gr, long_gr, pbt,
                        signal_score, sentiment_score, chart_url,
                        yahoo_price, last_action, per_portfolio, str(per_upside) if per_upside is not None else None
                    ))
                    
                    conn.commit()
                    success_count += 1
                    
                    print(f"    ✅ Saved {ticker_to_scrape} to database:")
                    print(f"       Rule1 Score: {rule1_score}")
                    print(f"       Signal Score: {signal_score}")
                    print(f"       Yahoo Price: ${yahoo_price}")
                    print(f"       Upside: {per_upside}%")
                
            except Exception as e:
                print(f"  ❌ Error processing {symbol}: {e}")
                conn.rollback()
        
        print(f"\n✅ Successfully saved {success_count} records to database")
        print("Note: Each ticker variant gets its own separate record")
        
    finally:
        driver.quit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()