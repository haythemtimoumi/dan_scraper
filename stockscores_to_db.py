#!/usr/bin/env python
import time
import psycopg2
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.browser import get_driver
from config.settings import DB_CONFIG

def scrape_stockscores_to_db():
    """
    Scrape tickers from StockScores and save directly to scraper_tasks table
    """
    driver = get_driver(headless=True)
    
    try:
        # Login to StockScores
        print("Navigating to StockScores login page...")
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
        
        # Navigate to scanner
        driver.get("https://www.stockscores.com/market-scan/scanner/")
        time.sleep(5)
        
        # Configure scan settings
        dropdown_button = driver.find_element(By.CSS_SELECTOR, ".btn.dropdown-toggle.btn-default")
        dropdown_button.click()
        time.sleep(2)
        
        option = driver.find_element(By.XPATH, "//span[contains(text(), 'Stockscores Basic Long')]")
        option.click()
        time.sleep(2)
        
        # Select NASDAQ
        exchange_dropdown = driver.find_element(By.CSS_SELECTOR, "button[data-id='exchange']")
        exchange_dropdown.click()
        time.sleep(1)
        
        nasdaq_option = driver.find_element(By.XPATH, "//span[text()='NASDAQ']")
        nasdaq_option.click()
        time.sleep(1)
        
        # Set market cap options
        script = """
        var select = document.getElementById('marketcap');
        for (var i = 0; i < select.options.length; i++) {
            select.options[i].selected = false;
        }
        for (var i = 0; i < select.options.length; i++) {
            if (select.options[i].value === 'mid' || select.options[i].value === 'large') {
                select.options[i].selected = true;
            }
        }
        var event = new Event('change');
        select.dispatchEvent(event);
        $(select).selectpicker('refresh');
        """
        driver.execute_script(script)
        time.sleep(1)
        
        # Set MaxResult to 999
        max_result_input = driver.find_element(By.NAME, "MaxResult")
        max_result_input.clear()
        max_result_input.send_keys("999")
        time.sleep(3)
        
        # Run scan
        run_scan_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Run Market Scan')]")
        run_scan_button.click()
        time.sleep(10)
        
        # Scrape tickers
        ticker_elements = driver.find_elements(By.XPATH, "//td[@align='left']/a[contains(@href, '/charts/charts/?ticker=')]")
        tickers = [element.text.strip() for element in ticker_elements if element.text.strip()]
        
        if tickers:
            print(f"Found {len(tickers)} ticker symbols")
            save_tickers_to_db(tickers)
        else:
            print("No ticker symbols found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

def save_tickers_to_db(tickers):
    """Save tickers to scraper_tasks table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get or create guru for stockscores
        cursor.execute("""
            INSERT INTO guru (guru_name, description) 
            VALUES (%s, %s) 
            ON CONFLICT (guru_name) DO NOTHING 
            RETURNING id
        """, ('stocks_lists', 'StockScores scanner results'))
        
        guru_result = cursor.fetchone()
        if guru_result:
            guru_id = guru_result[0]
        else:
            cursor.execute("SELECT id FROM guru WHERE guru_name = %s", ('stocks_lists',))
            guru_id = cursor.fetchone()[0]
        
        for ticker in tickers:
            cursor.execute("""
                INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type, active, scrape_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, guru_id, list_type) 
                DO UPDATE SET 
                    active = TRUE, 
                    scrape_status = CASE 
                        WHEN scraper_tasks.list_type = 'stockscore_list' THEN 'pending'
                        ELSE scraper_tasks.scrape_status
                    END
            """, (ticker, guru_id, 'stockscore_list', 'monthly', True, 'pending'))
        
        conn.commit()
        print(f"Successfully saved {len(tickers)} tickers to database")
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    scrape_stockscores_to_db()