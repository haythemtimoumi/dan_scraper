import os
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def get_dual_tickers():
    """Get only tickers that have a stock_ticker field"""
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
        AND stock_ticker IS NOT NULL 
        AND stock_ticker != '' 
        AND stock_ticker != symbol
        ORDER BY symbol
    """)
    
    tickers = cursor.fetchall()
    cursor.close()
    conn.close()
    return tickers

def login_stockscores(driver):
    driver.get("https://www.stockscores.com/login")
    try:
        username_field = driver.find_element(By.ID, "login-form-username")
        username_field.send_keys(os.getenv('STOCKSCORES_USERNAME'))
        
        password_field = driver.find_element(By.ID, "login-form-password")
        password_field.send_keys(os.getenv('STOCKSCORES_PASSWORD'))
        
        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()
    except:
        print("Login elements not found - may already be logged in")

def scrape_stockscores_data(driver, ticker):
    """Scrape only StockScores data"""
    url = f"https://www.stockscores.com/charts/charts/?ticker={ticker}"
    driver.get(url)
    
    try:
        score_elements = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[@style='font-size:24px;']/b"))
        )
        
        sentiment_score = score_elements[0].text if len(score_elements) > 0 else None
        signal_score = score_elements[1].text if len(score_elements) > 1 else None
        
        chart_img = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.changeWidth"))
        )
        chart_url = chart_img.get_attribute("src")
        
        return {
            'sentiment_score': sentiment_score,
            'signal_score': signal_score,
            'chart_url': chart_url
        }
    except:
        return {
            'sentiment_score': None,
            'signal_score': None,
            'chart_url': None
        }

def fetch_yahoo_price(ticker):
    """Fetch current price from Yahoo Finance"""
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
                        return price_rounded
        return None
    except Exception as e:
        print(f"    Error fetching Yahoo price for {ticker}: {e}")
        return None

def main():
    dual_tickers = get_dual_tickers()
    print(f"Found {len(dual_tickers)} tickers with stock_ticker field")
    
    if not dual_tickers:
        print("No dual tickers found")
        return
    
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
    driver = webdriver.Chrome(options=chrome_options)
    
    success_count = 0
    
    try:
        login_stockscores(driver)
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio, stock_ticker) in enumerate(dual_tickers, 1):
            print(f"\n[{i}/{len(dual_tickers)}] Processing {symbol} + {stock_ticker}")
            
            # Get Rule1 data from database
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
            else:
                rule1_score, moat_score, management_score, buy_price, full_name, last_gr, long_gr, pbt = (None, None, None, None, None, None, None, None)
            
            # Process both tickers
            for ticker_to_scrape in [symbol, stock_ticker]:
                print(f"  Scraping {ticker_to_scrape}...")
                
                # Get StockScores data
                stockscores_data = scrape_stockscores_data(driver, ticker_to_scrape)
                
                # Get Yahoo price
                yahoo_price = fetch_yahoo_price(ticker_to_scrape)
                
                # Calculate upside
                per_upside = None
                if buy_price and yahoo_price and yahoo_price > 0:
                    try:
                        buy_price_num = float(buy_price)
                        per_upside = round((2 * buy_price_num - yahoo_price) / yahoo_price * 100, 2)
                    except (ValueError, TypeError):
                        per_upside = None
                
                # Save to database
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
                    stockscores_data['signal_score'], stockscores_data['sentiment_score'], stockscores_data['chart_url'],
                    yahoo_price, last_action, per_portfolio, str(per_upside) if per_upside is not None else None
                ))
                
                conn.commit()
                success_count += 1
                
                print(f"    ✅ {ticker_to_scrape}: Signal={stockscores_data['signal_score']}, Price=${yahoo_price}, Upside={per_upside}%")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        driver.quit()
        cursor.close()
        conn.close()
        print(f"\n✅ Processed {success_count} ticker records")

if __name__ == "__main__":
    main()