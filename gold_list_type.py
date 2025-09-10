#!/usr/bin/env python
import os
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
from config.settings import DB_CONFIG

load_dotenv()

def login_goldstockdata():
    """Login to goldstockdata.com"""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-data-dir=/tmp/chrome_goldstock_' + str(int(time.time())))
    options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    try:
        # Navigate to login page
        print("Navigating to goldstockdata.com...")
        driver.get("https://www.goldstockdata.com/companies.html")
        time.sleep(3)
        
        print("Page loaded, looking for login form...")
        
        # Try different selectors for email field
        email_field = None
        selectors = [
            (By.NAME, "Email"),
            (By.CLASS_NAME, "email-placeholder"),
            (By.CSS_SELECTOR, 'input[name="Email"]'),
            (By.CSS_SELECTOR, 'input.email-placeholder')
        ]
        
        for selector_type, selector_value in selectors:
            try:
                email_field = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                print(f"Found email field with: {selector_type}={selector_value}")
                break
            except:
                continue
        
        if not email_field:
            print("Could not find email field. Page source:")
            print(driver.page_source[:1000])
            return None
        
        # Clear and fill email
        email_field.clear()
        email_field.send_keys(os.getenv('GOLDSTOCKDATA_EMAIL'))
        
        # Find password field
        password_field = driver.find_element(By.CSS_SELECTOR, 'input.passwd-placeholder')
        password_field.clear()
        password_field.send_keys(os.getenv('GOLDSTOCKDATA_PASSWORD'))
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value=" Login "]')
        login_button.click()
        
        time.sleep(3)
        print("Login successful!")
        return driver
        
    except Exception as e:
        print(f"Login failed: {e}")
        driver.quit()
        return None

def scrape_top25_tickers(driver):
    """Scrape ticker symbols from TOP25 page"""
    tickers = []
    
    # Find all ticker cells
    ticker_cells = driver.find_elements(By.CSS_SELECTOR, "td[title*='All Symbols:']")
    
    for cell in ticker_cells:
        ticker_text = cell.text.strip()
        if ticker_text:
            tickers.append(ticker_text)
            print(f"Found ticker: {ticker_text}")
    
    return tickers



def scrape_mormons_tickers(driver):
    """Scrape ticker symbols from Mormons preset search"""
    return scrape_preset_tickers(driver, "Mormons")

def scrape_preset_tickers(driver, preset_name):
    """Generic function to scrape ticker symbols from any preset search"""
    tickers = []
    
    # Check if this is the correct preset page
    try:
        header = driver.find_element(By.CSS_SELECTOR, "h2").text
        if f"Preset Search: {preset_name}" not in header:
            print(f"Not on {preset_name} page. Found header: {header}")
            return tickers
        print(f"Confirmed on {preset_name} page")
    except:
        print("Could not find page header")
        return tickers
    
    # Find all ticker cells
    ticker_cells = driver.find_elements(By.CSS_SELECTOR, "td[title*='All Symbols:']")
    
    for cell in ticker_cells:
        ticker_text = cell.text.strip()
        if ticker_text:
            tickers.append(ticker_text)
            print(f"Found {preset_name} ticker: {ticker_text}")
    
    return tickers

def process_tickers_with_category(tickers, category_name):
    """Process tickers and update database with specific category"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get dan's guru_id
    cursor.execute("SELECT id FROM guru WHERE guru_name = 'dan'")
    dan_guru_id = cursor.fetchone()[0]
    
    for ticker in tickers:
        try:
            # Check if ticker exists
            cursor.execute("SELECT id FROM scraper_tasks WHERE symbol = %s", (ticker,))
            result = cursor.fetchone()
            
            if result:
                # Ticker exists - add category
                ticker_id = result[0]
                cursor.execute("""
                    INSERT INTO stock_list_categories (ticker_id, category_name)
                    VALUES (%s, %s)
                    ON CONFLICT (ticker_id, category_name) DO NOTHING
                """, (ticker_id, category_name))
                print(f"Added {category_name} category to existing ticker {ticker}")
            else:
                # Ticker doesn't exist - create new entry
                cursor.execute("""
                    INSERT INTO scraper_tasks (symbol, guru_id, scrape_type, active)
                    VALUES (%s, %s, 'daily', false)
                    RETURNING id
                """, (ticker, dan_guru_id))
                ticker_id = cursor.fetchone()[0]
                
                # Add category
                cursor.execute("""
                    INSERT INTO stock_list_categories (ticker_id, category_name)
                    VALUES (%s, %s)
                """, (ticker_id, category_name))
                print(f"Added new ticker {ticker} with {category_name} category")
                
        except Exception as e:
            print(f"Error processing ticker {ticker}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()

def main():
    """Main function to login and scrape TOP25 and Mormons tickers"""
    driver = login_goldstockdata()
    
    if driver:
        try:
            # Scrape TOP25
            print("Navigating to TOP25 research page...")
            driver.get("https://www.goldstockdata.com/research.php?submitted=1&PresetSearchID=TOP25")
            time.sleep(3)
            
            tickers = scrape_top25_tickers(driver)
            print(f"Found {len(tickers)} TOP25 tickers")
            if tickers:
                process_tickers_with_category(tickers, 'top25')
                print("TOP25 database updated successfully!")
            
            # Scrape Mormons
            print("\nNavigating to Mormons research page...")
            driver.get("https://www.goldstockdata.com/research.php")
            time.sleep(2)
            
            # Select Mormons from dropdown
            try:
                dropdown = Select(driver.find_element(By.NAME, "NewsletterSearchID"))
                dropdown.select_by_value("D-1795")
                time.sleep(3)
                
                mormons_tickers = scrape_mormons_tickers(driver)
                print(f"Found {len(mormons_tickers)} Mormons tickers")
                if mormons_tickers:
                    process_tickers_with_category(mormons_tickers, 'mormons')
                    print("Mormons database updated successfully!")
            except Exception as e:
                print(f"Could not select Mormons from dropdown: {e}")
            
            # Scrape Top Picks
            print("\nNavigating to Top Picks...")
            try:
                dropdown = Select(driver.find_element(By.NAME, "NewsletterSearchID"))
                dropdown.select_by_value("D-945")
                time.sleep(3)
                
                top_picks_tickers = scrape_preset_tickers(driver, "Top Picks")
                print(f"Found {len(top_picks_tickers)} Top Picks tickers")
                if top_picks_tickers:
                    process_tickers_with_category(top_picks_tickers, 'top_picks')
                    print("Top Picks database updated successfully!")
            except Exception as e:
                print(f"Could not select Top Picks from dropdown: {e}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            driver.quit()
    else:
        print("Failed to login, cannot proceed.")

if __name__ == "__main__":
    main()