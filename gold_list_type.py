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
    """Scrape ticker symbols and URLs from TOP25 page"""
    return scrape_preset_tickers(driver, "Top 25")



def scrape_mormons_tickers(driver):
    """Scrape ticker symbols from Mormons preset search"""
    return scrape_preset_tickers(driver, "Mormons")

def scrape_preset_tickers(driver, preset_name):
    """Generic function to scrape ticker symbols and company URLs from any preset search"""
    companies = []
    
    # Check if this is the correct preset page
    try:
        header = driver.find_element(By.CSS_SELECTOR, "h2").text
        # Handle different header formats
        expected_headers = [f"Preset Search: {preset_name}", f"Preset Search: {preset_name} Stocks"]
        if not any(expected in header for expected in expected_headers):
            print(f"Not on {preset_name} page. Found header: {header}")
            return companies
        print(f"Confirmed on {preset_name} page")
    except:
        print("Could not find page header")
        return companies
    
    # Find all rows in the results table
    rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
    
    for row in rows:
        try:
            # Get ticker from cell with title containing "All Symbols:"
            ticker_cell = row.find_element(By.CSS_SELECTOR, "td[title*='All Symbols:']")
            ticker = ticker_cell.text.strip()
            
            # Get profile URL
            profile_link = row.find_element(By.CSS_SELECTOR, "a[href*='/company/']")
            company_url = profile_link.get_attribute('href')
            
            if ticker and company_url:
                # Make URL absolute
                if company_url.startswith('/'):
                    company_url = 'https://www.goldstockdata.com' + company_url
                
                companies.append({'ticker': ticker, 'url': company_url})
                print(f"Found {preset_name} ticker: {ticker}")
        except:
            continue
    
    return companies

def scrape_company_data(driver):
    """Scrape detailed company data from individual company page"""
    try:
        # Get company name
        company_name = ""
        try:
            company_name = driver.find_element(By.CSS_SELECTOR, "div.name h1").text.strip()
        except:
            pass
        
        # Get category
        category = driver.find_element(By.CSS_SELECTOR, "#rating-summary tr:first-child td:last-child b").text.strip()
        
        # Get upside/downside
        upside = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(1)").text.strip()
        downside = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(2)").text.strip()
        
        # Get quality
        try:
            quality = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(3) span").text.strip()
        except:
            quality = driver.find_element(By.CSS_SELECTOR, "#rating-matrix tr.data td:nth-child(3)").text.strip()
        
        # Get risk
        risk = driver.find_element(By.CSS_SELECTOR, "#rating-summary tr:last-child td:last-child b").text.strip()
        
        # Get symbol and price
        symbol = ""
        exchange = ""
        ticker = ""
        currency = ""
        price = ""
        
        try:
            main_row = driver.find_element(By.CSS_SELECTOR, "tr.main")
            symbol = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) b").text.strip()
            
            if ":" in symbol:
                exchange, ticker = symbol.split(":", 1)
            else:
                ticker = symbol
                exchange = ""
            
            currency = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
            price = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(6) b").text.strip()
            # Remove commas from price for database compatibility
            price = price.replace(',', '') if price else ''
        except:
            pass
        
        # Get financial metrics
        cash_flow_growth = ""
        try:
            cash_flow_growth = driver.find_element(By.CSS_SELECTOR, "#fv-33 td.current").text.strip()
        except:
            pass
        
        free_cash_multiple = ""
        try:
            free_cash_multiple = driver.find_element(By.CSS_SELECTOR, "#fv-110 td.current").text.strip()
        except:
            pass
        
        # Get contact info
        company_url = ""
        try:
            company_url_element = driver.find_element(By.CSS_SELECTOR, "span.es-nowrap a[href^='http']")
            company_url = company_url_element.get_attribute('href')
        except:
            pass
        
        company_email = ""
        try:
            company_email_element = driver.find_element(By.CSS_SELECTOR, "span.es-nowrap a[href^='mailto:']")
            company_email = company_email_element.get_attribute('href').replace('mailto:', '')
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
            'free_cash_multiple': free_cash_multiple,
            'company_url': company_url,
            'company_email': company_email
        }
    except Exception as e:
        print(f"Error scraping company data: {e}")
        return None

def process_companies_with_category(driver, companies, category_name):
    """Visit each company page, scrape data, and save to database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get dan's guru_id
    cursor.execute("SELECT id FROM guru WHERE guru_name = 'dan'")
    dan_guru_id = cursor.fetchone()[0]
    
    for i, company in enumerate(companies):
        print(f"Scraping {company['ticker']} ({i+1}/{len(companies)})")
        
        try:
            # Check if ticker exists
            cursor.execute("SELECT id FROM scraper_tasks WHERE symbol = %s", (company['ticker'],))
            result = cursor.fetchone()
            
            if result:
                ticker_id = result[0]
            else:
                # Create new ticker entry
                cursor.execute("""
                    INSERT INTO scraper_tasks (symbol, guru_id, scrape_type, active)
                    VALUES (%s, %s, 'daily', false)
                    RETURNING id
                """, (company['ticker'], dan_guru_id))
                ticker_id = cursor.fetchone()[0]
            
            # Add category
            cursor.execute("""
                INSERT INTO stock_list_categories (ticker_id, category_name)
                VALUES (%s, %s)
                ON CONFLICT (ticker_id, category_name) DO NOTHING
            """, (ticker_id, category_name))
            
            # Visit company page and scrape detailed data
            driver.get(company['url'])
            time.sleep(2)
            
            company_data = scrape_company_data(driver)
            if company_data:
                print(f"Scraped data for {company['ticker']}:")
                print(f"  Company: {company_data['company_name']}")
                print(f"  Price: {company_data['price']} {company_data['currency']}")
                print(f"  Category: {company_data['category']}")
                print(f"  Upside: {company_data['upside']}, Downside: {company_data['downside']}")
                print(f"  Quality: {company_data['quality']}, Risk: {company_data['risk']}")
                print(f"  Cash Flow Growth: {company_data['cash_flow_growth']}")
                print(f"  Free Cash Multiple: {company_data['free_cash_multiple']}")
                print(f"  Website: {company_data['company_url']}")
                print(f"  Email: {company_data['company_email']}")
                
                # Insert new company data (daily snapshot)
                cursor.execute("""
                    INSERT INTO company (
                        ticker_id, company_name, full_symbol, exchange, currency,
                        price, category, upside, downside, quality, risk,
                        cash_flow_growth, free_cash_multiple, source_url,
                        company_url, company_email
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    ticker_id, company_data['company_name'], company_data['symbol'],
                    company_data['exchange'], company_data['currency'], company_data['price'],
                    company_data['category'], company_data['upside'], company_data['downside'],
                    company_data['quality'], company_data['risk'], company_data['cash_flow_growth'],
                    company_data['free_cash_multiple'], company['url'],
                    company_data['company_url'], company_data['company_email']
                ))
                print(f"✓ Saved to database\n")
            
        except Exception as e:
            print(f"Error processing company {company['ticker']}: {e}")
            conn.rollback()  # Rollback failed transaction
            continue
    
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
                process_companies_with_category(driver, tickers, 'top25')
                print("TOP25 database updated successfully!")
            
            # Scrape Mormons
            print("\nNavigating to Mormons research page...")
            driver.get("https://www.goldstockdata.com/research.php")
            time.sleep(2)
            
            # Select Mormons from dropdown
            try:
                # Wait for page to load completely
                wait = WebDriverWait(driver, 10)
                dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "NewsletterSearchID")))
                dropdown = Select(dropdown_element)
                dropdown.select_by_value("D-1795")
                time.sleep(3)
                
                mormons_tickers = scrape_mormons_tickers(driver)
                print(f"Found {len(mormons_tickers)} Mormons tickers")
                if mormons_tickers:
                    process_companies_with_category(driver, mormons_tickers, 'mormons')
                    print("Mormons database updated successfully!")
            except Exception as e:
                print(f"Could not select Mormons from dropdown: {e}")
            
            # Scrape Top Picks
            print("\nNavigating to Top Picks...")
            try:
                # Navigate back to research page first
                driver.get("https://www.goldstockdata.com/research.php")
                time.sleep(3)
                
                # Wait for dropdown to be available
                wait = WebDriverWait(driver, 10)
                dropdown_element = wait.until(EC.presence_of_element_located((By.NAME, "NewsletterSearchID")))
                dropdown = Select(dropdown_element)
                dropdown.select_by_value("D-945")
                time.sleep(3)
                
                top_picks_tickers = scrape_preset_tickers(driver, "Top Picks")
                print(f"Found {len(top_picks_tickers)} Top Picks tickers")
                if top_picks_tickers:
                    process_companies_with_category(driver, top_picks_tickers, 'top_picks')
                    print("Top Picks database updated successfully!")
            except Exception as e:
                print(f"Could not select Top Picks from dropdown: {e}")
                print(f"Current URL: {driver.current_url}")
                # Try to find what elements are available
                try:
                    dropdowns = driver.find_elements(By.TAG_NAME, "select")
                    print(f"Found {len(dropdowns)} dropdown elements on page")
                except:
                    print("No dropdown elements found")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            driver.quit()
    else:
        print("Failed to login, cannot proceed.")

if __name__ == "__main__":
    main()