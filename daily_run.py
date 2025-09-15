#!/usr/bin/env python
"""
Process active tickers with:
1. Reused Rule1 data from current month
2. Fresh StockScores data using direct scraping logic
3. Fresh Price data
"""

import os
import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import time

load_dotenv()

def get_chrome_driver():
    """Get Chrome driver with options"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def login_stockscores(driver):
    """Login to StockScores"""
    driver.get("https://www.stockscores.com/my-account/")
    
    if "login" not in driver.current_url.lower():
        print("Already logged in to StockScores")
        return True
    
    try:
        email_field = driver.find_element(By.ID, "login-form-username")
        email_field.send_keys(os.getenv('STOCKSCORES_EMAIL'))
        
        password_field = driver.find_element(By.ID, "login-form-password")
        password_field.send_keys(os.getenv('STOCKSCORES_PASSWORD'))
        
        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()
        return True
    except Exception as e:
        print(f"StockScores login failed: {e}")
        return False

def scrape_ticker_data(driver, ticker):
    """Scrape StockScores data for single ticker"""
    url = f"https://www.stockscores.com/charts/charts/?ticker={ticker}"
    driver.get(url)
    
    try:
        score_elements = WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[@style='font-size:24px;']/b"))
        )
        
        sentiment_score = score_elements[0].text if len(score_elements) > 0 else "N/A"
        signal_score = score_elements[1].text if len(score_elements) > 1 else "N/A"
        
        # Get chart image URL
        try:
            chart_img = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.changeWidth"))
            )
            chart_url = chart_img.get_attribute("src")
        except:
            chart_url = "N/A"
        
        return signal_score, sentiment_score, chart_url
        
    except Exception as e:
        print(f"Timeout/Error scraping {ticker}: {e}")
        return "N/A", "N/A", "N/A"

def fetch_price(ticker):
    """Fetch current price from Yahoo Finance"""
    try:
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    price = result['meta']['regularMarketPrice']
                    return round(float(price), 2) if price else None
    except:
        pass
    return None

def run_active_direct():
    """Run process for active tickers with direct StockScores scraping"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Starting active ticker direct process at {current_time}...\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get active tickers
        cursor.execute("SELECT id, symbol, guru_id, list_type, last_action, per_portfolio FROM scraper_tasks WHERE active = true")
        active_tickers = cursor.fetchall()
        
        if not active_tickers:
            print("❌ No active tickers found")
            return 0
        
        print(f"Processing {len(active_tickers)} active tickers...\n")
        
        # Initialize StockScores driver
        driver = get_chrome_driver()
        login_stockscores(driver)
        
        success_count = 0
        
        for i, (ticker_id, symbol, guru_id, list_type, last_action, per_portfolio) in enumerate(active_tickers, 1):
            print(f"[{i}/{len(active_tickers)}] Processing {symbol}...")
            
            try:
                # Get Rule1 data from most recent record this month
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
                
                # Get fresh StockScores data using direct scraping
                signal_score, sentiment_score, screenshot = scrape_ticker_data(driver, symbol)
                
                # Get fresh Price data
                price = fetch_price(symbol)
                
                # Calculate per_upside
                per_upside = None
                if buy_price and price and price > 0:
                    try:
                        buy_price_num = float(buy_price)
                        per_upside = round((2 * buy_price_num - price) / price * 100, 2)
                    except (ValueError, TypeError):
                        per_upside = None
                
                # Create complete record
                cursor.execute("""
                    INSERT INTO stock_analysis (
                        ticker_id, guru_id, date, ticker, source,
                        rule1_score, moat_score, management_score, buy_price,
                        full_name, last_gr, long_gr, pbt,
                        signal_score, sentiment_score, screenshot,
                        last_price, last_action, per_portfolio, per_upside
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker_id, guru_id, current_time, symbol, list_type,
                    rule1_score, moat_score, management_score, buy_price,
                    full_name, last_gr, long_gr, pbt,
                    signal_score if signal_score != 'N/A' else None,
                    sentiment_score if sentiment_score != 'N/A' else None,
                    screenshot if screenshot != 'N/A' else None,
                    price, last_action, per_portfolio, str(per_upside) if per_upside is not None else None
                ))
                
                success_count += 1
                print(f"Complete record created: Rule1={rule1_score}, Signal={signal_score}, Price=${price}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        conn.commit()
        driver.quit()
        
        print(f"\nActive ticker direct process completed: {success_count}/{len(active_tickers)} complete records created")
        
        # Send Firebase notification
        from firebase_notifier import FirebaseNotifier
        FirebaseNotifier.send_notification(
            title="Scraper Complete",
            body=f"Active ticker direct scraper finished: {success_count}/{len(active_tickers)} records",
            data={"script": "scrape_active_direct", "success_count": str(success_count), "total_count": str(len(active_tickers)), "timestamp": str(datetime.now())}
        )
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_active_direct()