#!/usr/bin/env python
import time
import psycopg2
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.browser_minimal import get_minimal_driver
from config.settings import DB_CONFIG

def scrape_dan_watchlist_to_db():
    """
    Login to StockScores, navigate to watchlist creator, scrape tickers and save to database
    """
    driver = get_minimal_driver(headless=True)
    
    try:
        # STEP 0: Login to StockScores
        print("STEP 0: Login to StockScores")
        driver.get("https://www.stockscores.com/my-account/")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-form-username"))
        )
        
        # Enter credentials
        username_field = driver.find_element(By.ID, "login-form-username")
        password_field = driver.find_element(By.ID, "login-form-password")
        
        username_field.clear()
        username_field.send_keys("Stock@tundraeng.com")
        password_field.clear()
        password_field.send_keys("56Stingray#")
        
        login_button = driver.find_element(By.ID, "login-form-submit")
        login_button.click()
        time.sleep(5)
        print("Successfully logged in to StockScores")
        
        # STEP 2: Navigate to watchlist creator
        print("STEP 2: Navigate to watchlist creator")
        driver.get("https://www.stockscores.com/charts/watchlist-creator/")
        time.sleep(5)
        print("Successfully navigated to watchlist creator")
        
        # STEP 3: Scrape tickers
        print("STEP 3: Scrape tickers")
        tickers = scrape_watchlist_tickers(driver)
        
        if tickers:
            print(f"Found {len(tickers)} ticker symbols")
            # STEP 4: Save to database
            save_dan_watchlist_to_db(tickers)
        else:
            print("No ticker symbols found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

def scrape_watchlist_tickers(driver):
    """Scrape ticker symbols from the watchlist creator page"""
    tickers = []
    
    try:
        # Wait for page to load
        time.sleep(3)
        
        # Use the exact selector for the ticker format
        elements = driver.find_elements(By.XPATH, "//td[@align='left']/strong/a[contains(@href, '/charts/charts/?ticker=')]")
        
        for element in elements:
            ticker_text = element.text.strip()
            if ticker_text and len(ticker_text) <= 5 and ticker_text.isupper():
                tickers.append(ticker_text)
                print(f"Found ticker: {ticker_text}")
        
        # Remove duplicates
        tickers = list(set(tickers))
        
    except Exception as e:
        print(f"Error scraping tickers: {e}")
    
    return tickers

def save_dan_watchlist_to_db(tickers):
    """Save Dan's watchlist tickers to scraper_tasks table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get or create guru for dan
        cursor.execute("""
            INSERT INTO guru (guru_name, description) 
            VALUES (%s, %s) 
            ON CONFLICT (guru_name) DO NOTHING 
            RETURNING id
        """, ('dan', 'Dan portfolio watchlist'))
        
        guru_result = cursor.fetchone()
        if guru_result:
            guru_id = guru_result[0]
        else:
            cursor.execute("SELECT id FROM guru WHERE guru_name = %s", ('dan',))
            guru_id = cursor.fetchone()[0]
        
        for ticker in tickers:
            cursor.execute("""
                INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type, active, scrape_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, guru_id, list_type) 
                DO UPDATE SET 
                    active = TRUE,
                    scrape_status = CASE 
                        WHEN scraper_tasks.list_type = 'dan_portfolio_list' THEN 'pending'
                        ELSE scraper_tasks.scrape_status
                    END
            """, (ticker, guru_id, 'dan_portfolio_list', 'monthly', True, 'pending'))
        
        conn.commit()
        print(f"Saved {len(tickers)} tickers to database with guru='dan' and list_type='dan_portfolio_list'")
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    scrape_dan_watchlist_to_db()