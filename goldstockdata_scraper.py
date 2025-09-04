#!/usr/bin/env python
import os
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def scrape_companies(driver):
    """Scrape all company names and URLs"""
    companies = []
    
    # Find all company links using the correct pattern
    company_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
    
    for link in company_links:
        company_name = link.text.strip()
        company_url = link.get_attribute('href')
        
        if company_name and company_url and not company_name.startswith('['):
            # Make URL absolute if needed
            if company_url.startswith('/'):
                company_url = 'https://www.goldstockdata.com' + company_url
            
            # Skip URLs with query parameters
            if '?' not in company_url:
                companies.append({'name': company_name, 'url': company_url})
                print(f"Found: {company_name} - {company_url}")
    
    return companies

def scrape_rating_data(driver):
    """Scrape rating data from company page"""
    try:
        # Get company name from h1
        company_name = ""
        try:
            company_name = driver.find_element(By.CSS_SELECTOR, "div.name h1").text.strip()
        except:
            pass
        
        # Get category - "Major"
        category = driver.find_element(By.CSS_SELECTOR, "#rating-summary tr:first-child td:last-child b").text.strip()
        
        # Get upside - "2.5" 
        upside = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(1)").text.strip()
        
        # Get downside - "3.5"
        downside = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(2)").text.strip()
        
        # Get quality - "A-" (from span inside the cell)
        try:
            quality = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(3) span").text.strip()
        except:
            quality = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(3)").text.strip()
        
        # Get risk - "Some"
        risk = driver.find_element(By.CSS_SELECTOR, "#rating-summary tr:last-child td:last-child b").text.strip()
        
        # Get symbol and price from main table
        symbol = ""
        exchange = ""
        ticker = ""
        currency = ""
        price = ""
        
        try:
            main_row = driver.find_element(By.CSS_SELECTOR, "tr.main")
            symbol = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) b").text.strip()
            
            # Split symbol into exchange and ticker (e.g., "CVE:ALTA" -> "CVE" and "ALTA")
            if ":" in symbol:
                exchange, ticker = symbol.split(":", 1)
            else:
                ticker = symbol
                exchange = ""
            
            currency = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
            price = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(6) b").text.strip()
        except:
            pass
        
        # Get cash flow growth
        cash_flow_growth = ""
        try:
            cash_flow_growth = driver.find_element(By.CSS_SELECTOR, "#fv-33 td.current").text.strip()
        except:
            pass
        
        # Get free cash multiple
        free_cash_multiple = ""
        try:
            free_cash_multiple = driver.find_element(By.CSS_SELECTOR, "#fv-110 td.current").text.strip()
        except:
            pass
        
        return {
            'company_name': company_name,
            'category': category,
            'upside': upside,
            'downside': downside,
            'quality': quality,
            'risk': risk,
            'symbol': symbol,
            'exchange': exchange,
            'ticker': ticker,
            'currency': currency,
            'price': price,
            'cash_flow_growth': cash_flow_growth,
            'free_cash_multiple': free_cash_multiple
        }
    except Exception as e:
        print(f"Error scraping rating data: {e}")
        return None

def visit_all_companies(driver, companies):
    """Visit each company URL and scrape rating data, save to database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    success_count = 0
    
    # Get dan's guru_id
    cursor.execute("SELECT id FROM guru WHERE guru_name = 'dan'")
    dan_guru_id = cursor.fetchone()[0]
    
    for i, company in enumerate(companies):
        print(f"Scraping {company['name']} ({i+1}/{len(companies)})")
        driver.get(company['url'])
        time.sleep(2)
        
        rating_data = scrape_rating_data(driver)
        if rating_data and rating_data['ticker']:
            try:
                # Insert or get existing ticker
                cursor.execute("""
                    INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type)
                    VALUES (%s, %s, 'gold', 'daily')
                    ON CONFLICT (symbol) DO UPDATE SET last_updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (rating_data['ticker'], dan_guru_id))
                ticker_id = cursor.fetchone()[0]
                
                # Insert company data
                cursor.execute("""
                    INSERT INTO company (
                        ticker_id, company_name, full_symbol, exchange, currency,
                        price, category, upside, downside, quality, risk,
                        cash_flow_growth, free_cash_multiple, source_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker_id, rating_data['company_name'], rating_data['symbol'],
                    rating_data['exchange'], rating_data['currency'],
                    float(rating_data['price'].replace(',', '')) if rating_data['price'] else None,
                    rating_data['category'], 
                    float(rating_data['upside'].replace(',', '')) if rating_data['upside'] else None,
                    float(rating_data['downside'].replace(',', '')) if rating_data['downside'] else None,
                    rating_data['quality'], rating_data['risk'],
                    rating_data['cash_flow_growth'],
                    float(rating_data['free_cash_multiple'].replace(',', '')) if rating_data['free_cash_multiple'] else None,
                    company['url']
                ))
                
                conn.commit()
                success_count += 1
                print(f"  ✅ {rating_data['ticker']} - {rating_data['currency']} {rating_data['price']} - {rating_data['quality']}")
                print(f"     Category: {rating_data['category']}, Upside: {rating_data['upside']}, Downside: {rating_data['downside']}, Risk: {rating_data['risk']}")
                print(f"     Cash Flow Growth: {rating_data['cash_flow_growth']}, Free Cash Multiple: {rating_data['free_cash_multiple']}")
                print(f"     Exchange: {rating_data['exchange']}, Full Symbol: {rating_data['symbol']}")
                print(f"     Company: {rating_data['company_name']}")
                print()
                
            except Exception as e:
                print(f"  ❌ Error saving {rating_data['ticker']}: {e}")
                conn.rollback()
        else:
            print("  No rating data found")
    
    cursor.close()
    conn.close()
    print(f"\nData saved to database: {success_count}/{len(companies)} successful")
    return success_count

if __name__ == "__main__":
    from datetime import datetime
    
    driver = login_goldstockdata()
    if driver:
        companies = scrape_companies(driver)
        print(f"\nFound {len(companies)} companies")
        
        success_count = 0
        if companies:
            success_count = visit_all_companies(driver, companies)
        
        # Send email notification
        try:
            from utils.email_notifier import send_completion_email
            send_completion_email(
                recipient_email="dan.moore@tundraeng.com",
                success_count=success_count,
                total_count=len(companies),
                process_name="Gold Stock Data Scraping"
            )
        except Exception as e:
            print(f"Email notification failed: {e}")
        
        # Send Firebase notification
        try:
            from firebase_notifier import FirebaseNotifier
            FirebaseNotifier.send_notification(
                title="Gold Scraper Complete",
                body=f"Gold stock scraper finished: {success_count}/{len(companies)} companies",
                data={"script": "goldstockdata_scraper", "success_count": str(success_count), "total_count": str(len(companies)), "timestamp": str(datetime.now())}
            )
        except Exception as e:
            print(f"Firebase notification failed: {e}")
        
        driver.quit()