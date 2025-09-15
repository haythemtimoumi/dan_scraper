#!/usr/bin/env python
"""
Verify tickers on StockScores by checking for redirects to error page
"""

import os
import psycopg2
from config.settings import DB_CONFIG
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
        time.sleep(2)
        return True
    except Exception as e:
        print(f"StockScores login failed: {e}")
        return False

def check_ticker_validity(driver, ticker):
    """Check if ticker is valid on StockScores"""
    url = f"https://www.stockscores.com/charts/charts/?ticker={ticker}"
    driver.get(url)
    time.sleep(1)
    
    # Check if redirected to error page
    current_url = driver.current_url
    return "symbol-search" not in current_url and "err=symbol+not+found" not in current_url

def verify_all_tickers():
    """Verify all tickers in database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get all tickers
        cursor.execute("SELECT id, symbol FROM scraper_tasks ORDER BY symbol")
        tickers = cursor.fetchall()
        
        print(f"Checking {len(tickers)} tickers on StockScores...\n")
        
        driver = get_chrome_driver()
        login_stockscores(driver)
        
        invalid_tickers = []
        
        for i, (ticker_id, symbol) in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] Checking {symbol}...", end=" ")
            
            try:
                is_valid = check_ticker_validity(driver, symbol)
                if is_valid:
                    print("✓ Valid")
                else:
                    print("✗ Invalid")
                    invalid_tickers.append(symbol)
            except Exception as e:
                print(f"Error: {e}")
                invalid_tickers.append(symbol)
        
        driver.quit()
        
        print(f"\n{'='*50}")
        print(f"VERIFICATION COMPLETE")
        print(f"{'='*50}")
        print(f"Total tickers checked: {len(tickers)}")
        print(f"Invalid tickers found: {len(invalid_tickers)}")
        
        if invalid_tickers:
            print(f"\nINVALID TICKERS:")
            for ticker in invalid_tickers:
                print(f"  - {ticker}")
        else:
            print("\n✓ All tickers are valid!")
        
        return invalid_tickers
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_all_tickers()