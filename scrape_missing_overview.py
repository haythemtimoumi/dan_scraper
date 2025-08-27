#!/usr/bin/env python
"""
Scrape Company Overview for Missing Data
Targets tickers that don't have company overview data and scrapes them using Rule1Toolbox
"""

import psycopg2
from datetime import datetime
from config.settings import DB_CONFIG
from scrapers.scores_scraper import TickerSearcher

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def get_missing_overview_tickers():
    """Get tickers that are missing company overview data"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT id, symbol 
        FROM scraper_tasks 
        WHERE active = true 
        AND (business_description IS NULL OR business_description = '')
        AND (address IS NULL OR address = '')
        AND (website IS NULL OR website = '')
        AND (ir_phone_number IS NULL OR ir_phone_number = '')
        AND (email_address IS NULL OR email_address = '')
        AND year_established IS NULL
        AND fiscal_year_end IS NULL
        AND (ceo IS NULL OR ceo = '')
        AND number_of_employees IS NULL
        AND (sp IS NULL OR sp = '')
        ORDER BY id
    """)
    
    missing_tickers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return missing_tickers

def scrape_company_overview(driver, symbol):
    """Scrape company overview data for a ticker"""
    try:
        print(f"  → Navigating to {symbol} overview...")
        
        driver.get("https://ruleonetoolbox.com/explore/stocks")
        
        search_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Search for Stocks, Gurus"]'))
        )
        search_input.clear()
        search_input.send_keys(symbol)
        search_input.send_keys('\n')
        
        WebDriverWait(driver, 15).until(
            lambda d: "/ticker/" in d.current_url
        )
        
        if "/ticker/" not in driver.current_url:
            print(f"  ⚠️ {symbol} not found in Rule1Toolbox")
            return None
        
        try:
            overview_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(@class, "p-accordion-header-text") and contains(text(), "Overview")]'))
            )
            overview_button.click()
            print(f"  Clicked Overview accordion for {symbol}")
            
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "p-accordion-content")]'))
            )
            
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(3)
            
        except TimeoutException:
            print(f"  Overview accordion button not found for {symbol}")
            return None
        
        overview_data = {}
        
        field_mappings = {
            'business_description': [
                '//div[contains(@class, "title") and normalize-space(text())="Business Description"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "Business Description")]/following-sibling::div'
            ],
            'address': [
                '//div[contains(@class, "title") and normalize-space(text())="Address"]/following-sibling::div[contains(@class, "description")]//a',
                '//div[contains(text(), "Address")]/following-sibling::div//a'
            ],
            'website': [
                '//div[contains(@class, "title") and normalize-space(text())="Website"]/following-sibling::div[contains(@class, "description")]//a',
                '//div[contains(text(), "Website")]/following-sibling::div//a'
            ],
            'ir_phone': [
                '//div[contains(@class, "title") and normalize-space(text())="IR Phone Number"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "IR Phone Number")]/following-sibling::div'
            ],
            'email_address': [
                '//div[contains(@class, "title") and normalize-space(text())="Email Address"]/following-sibling::div[contains(@class, "description")]//a',
                '//div[contains(text(), "Email Address")]/following-sibling::div//a'
            ],
            'year_established': [
                '//div[contains(@class, "title") and normalize-space(text())="Year Established"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "Year Established")]/following-sibling::div'
            ],
            'fiscal_year_end': [
                '//div[contains(@class, "title") and normalize-space(text())="Fiscal Year End"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "Fiscal Year End")]/following-sibling::div'
            ],
            'ceo': [
                '//div[contains(@class, "title") and normalize-space(text())="CEO"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "CEO")]/following-sibling::div'
            ],
            'num_employees': [
                '//div[contains(@class, "title") and normalize-space(text())="Number of Employees"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "Number of Employees")]/following-sibling::div'
            ],
            'sp_index': [
                '//div[contains(@class, "title") and normalize-space(text())="S&P"]/following-sibling::div[contains(@class, "description")]',
                '//div[contains(text(), "S&P")]/following-sibling::div'
            ]
        }
        
        for field, selectors in field_mappings.items():
            value = None
            
            # Try each selector with retry logic
            for attempt in range(2):  # Try twice
                for selector in selectors:
                    try:
                        if attempt == 1:  # Second attempt - scroll and wait
                            driver.execute_script("window.scrollBy(0, 200);")
                            time.sleep(1)
                        
                        element = driver.find_element(By.XPATH, selector)
                        if field in ['website', 'email_address']:
                            href = element.get_attribute('href')
                            if href:
                                if field == 'email_address':
                                    value = href.replace('mailto:', '')
                                else:
                                    value = href
                        elif field == 'address':
                            value = element.text.strip()
                        elif field == 'year_established':
                            try:
                                value = int(element.text.strip())
                            except ValueError:
                                value = None
                        elif field == 'num_employees':
                            try:
                                emp_text = element.text.strip().replace(',', '')
                                value = int(emp_text)
                            except ValueError:
                                value = None
                        else:
                            value = element.text.strip() if element.text.strip() else None
                        
                        if value:
                            break
                            
                    except NoSuchElementException:
                        continue
                
                if value:  # Found value, no need to retry
                    break
            
            overview_data[field] = value
            if value:
                print(f"    Found {field}: {value}")
        
        found_fields = sum(1 for v in overview_data.values() if v is not None)
        print(f"  Scraped overview data for {symbol}: {found_fields}/10 fields found")
        return overview_data if found_fields > 0 else None
        
    except Exception as e:
        print(f"  Error scraping overview for {symbol}: {e}")
        return None

def run_missing_overview_scraping():
    """Run company overview scraping for tickers missing data"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Starting missing overview data scraping at {current_time}...\n")
    
    # Get tickers missing overview data
    missing_tickers = get_missing_overview_tickers()
    
    if not missing_tickers:
        print("No tickers missing overview data found")
        return 0
    
    print(f"Found {len(missing_tickers)} tickers missing overview data\n")
    
    # Initialize browser and scraper
    try:
        from core.browser_stable import get_stable_driver
        print("Initializing shared browser session...")
        shared_driver = get_stable_driver(headless=True)
        
        rule1_searcher = TickerSearcher(driver=shared_driver)
        
        print("Attempting Rule1 login...")
        login_result = rule1_searcher.login(auto_verify=True)
        
        if not login_result:
            print("Rule1 login failed")
            return 0
        else:
            print("Rule1 login successful\n")
            
    except Exception as e:
        print(f"Error initializing: {e}")
        return 0
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    success_count = 0
    
    try:
        for i, (ticker_id, symbol) in enumerate(missing_tickers, 1):
            print(f"[{i}/{len(missing_tickers)}] Processing {symbol}...")
            
            try:
                overview_data = scrape_company_overview(shared_driver, symbol)
                
                if overview_data:
                    cursor.execute("""
                        UPDATE scraper_tasks SET
                            business_description = %s,
                            address = %s,
                            website = %s,
                            ir_phone_number = %s,
                            email_address = %s,
                            year_established = %s,
                            fiscal_year_end = %s,
                            ceo = %s,
                            number_of_employees = %s,
                            sp = %s,
                            last_updated_at = %s
                        WHERE id = %s
                    """, (
                        overview_data.get('business_description'),
                        overview_data.get('address'),
                        overview_data.get('website'),
                        overview_data.get('ir_phone'),
                        overview_data.get('email_address'),
                        overview_data.get('year_established'),
                        overview_data.get('fiscal_year_end'),
                        overview_data.get('ceo'),
                        overview_data.get('num_employees'),
                        overview_data.get('sp_index'),
                        current_time,
                        ticker_id
                    ))
                    
                    success_count += 1
                    print(f"Overview data saved for {symbol}")
                else:
                    print(f"⚠️ No overview data found for {symbol}")
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        
        conn.commit()
        
    finally:
        cursor.close()
        conn.close()
        
        try:
            if 'shared_driver' in locals():
                shared_driver.quit()
                print("Browser session closed")
        except Exception as e:
            print(f"Warning: Error closing browser: {e}")
    
    print(f"\nMissing overview scraping completed: {success_count}/{len(missing_tickers)} successful")
    return success_count

if __name__ == "__main__":
    run_missing_overview_scraping()