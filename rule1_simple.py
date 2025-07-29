#!/usr/bin/env python
import psycopg2
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from core.browser_simple import get_simple_driver, kill_chrome_processes
from config.settings import DB_CONFIG

load_dotenv()

def simple_rule1_login(driver):
    """Simple login to Rule1Toolbox"""
    email = os.getenv("RULE1_EMAIL")
    if not email:
        raise ValueError("Missing RULE1_EMAIL in .env")
    
    print("Opening Rule1 login page...")
    driver.get("https://ruleonetoolbox.com/login")
    time.sleep(3)
    
    # Enter email
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Email Address"]'))
    )
    email_input.clear()
    email_input.send_keys(email)
    print(f"Entered email: {email}")
    
    # Click login button
    login_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[.//span[text()="Log In To Toolbox"]]'))
    )
    login_btn.click()
    print("Clicked login button")
    
    # Manual verification
    verification_code = input("Enter the email verification code: ")
    
    # Enter verification code
    try:
        # Try single field first
        code_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="text" and contains(@class, "verification-code")]'))
        )
        code_input.clear()
        code_input.send_keys(verification_code)
        print("Entered verification code in single field")
    except:
        # Try individual fields
        code_inputs = driver.find_elements(By.XPATH, '//input[@type="text" and @inputmode="numeric"]')
        if len(code_inputs) == 6:
            for i, digit in enumerate(verification_code):
                code_inputs[i].send_keys(digit)
            print("Entered verification code in individual fields")
        else:
            raise Exception("Could not find verification code input fields")
    
    time.sleep(5)
    
    # Check if login successful
    current_url = driver.current_url
    if "login" not in current_url.lower():
        print("✅ Login successful")
        return True
    else:
        print("❌ Login failed")
        return False

def navigate_to_stock_scan(driver):
    """Navigate to stock scan page"""
    print("Navigating to Stock Scan page...")
    
    # Hover over Explore menu
    explore_menu = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//a[@id="primaryMenuItemExplore"]'))
    )
    ActionChains(driver).move_to_element(explore_menu).perform()
    print("Hovered over Explore menu")
    
    # Click Scan for Stocks
    scan_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//span[text()="Scan for Stocks"]'))
    )
    scan_link.click()
    print("Clicked Scan for Stocks")
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(EC.url_contains("/explore/stocks"))
    print("✅ Successfully navigated to Stock Scan page")
    return True

def configure_rule_one_scores(driver):
    """Configure Rule One Scores to 85"""
    print("Configuring Rule One Scores...")
    
    # Expand Rule One Scores section
    try:
        accordion = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '//div[contains(text(), "Rule One Scores") and contains(@class, "scan-filters__group-name")]'
            ))
        )
        if 'p-accordion-tab-active' not in accordion.find_element(By.XPATH, './ancestor::div[contains(@class, "p-accordion-tab")]').get_attribute('class'):
            accordion.click()
            print("Expanded Rule One Scores section")
            time.sleep(1)
    except Exception as e:
        print(f"Could not expand Rule One Scores section: {e}")
    
    # Configure each score
    score_names = ["Moat Score", "Management Score", "Rule One Score"]
    
    for score_name in score_names:
        try:
            print(f"Configuring {score_name}...")
            
            # Check the checkbox
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f'//label[contains(@class, "p-checkbox-label") and contains(text(), "{score_name}")]/preceding-sibling::div[contains(@class, "p-checkbox")]'
                ))
            )
            
            if 'p-checkbox-checked' not in checkbox.get_attribute('class'):
                checkbox.click()
                print(f"Checked {score_name} checkbox")
                time.sleep(0.5)
            
            # Set value to 85
            input_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f'//label[contains(@class, "p-checkbox-label") and contains(text(), "{score_name}")]/ancestor::div[contains(@class, "scan-criterion")]//input[contains(@class, "p-inputnumber-input")]'
                ))
            )
            
            input_field.clear()
            time.sleep(0.2)
            input_field.send_keys("85")
            time.sleep(0.2)
            input_field.send_keys(Keys.ENTER)
            time.sleep(0.5)
            
            print(f"Set {score_name} to 85")
            
        except Exception as e:
            print(f"Error configuring {score_name}: {e}")
            continue
    
    print("✅ Configured Rule One Scores")
    return True

def apply_filter(driver):
    """Apply the filter"""
    print("Applying filter...")
    
    try:
        # Find any input field and press Enter
        input_field = driver.find_element(By.XPATH, '//input[contains(@class, "p-inputnumber-input")]')
        input_field.send_keys(Keys.ENTER)
        print("Pressed Enter to apply filter")
        
        # Wait for loading to complete
        time.sleep(3)
        
        print("✅ Filter applied")
        return True
        
    except Exception as e:
        print(f"Error applying filter: {e}")
        return False

def scrape_tickers(driver):
    """Scrape ticker symbols from the results table"""
    print("Scraping ticker symbols...")
    
    # Wait for table to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '//tbody[contains(@class, "p-datatable-tbody")]'))
    )
    
    tickers = []
    current_page = 1
    max_pages = 10
    
    while current_page <= max_pages:
        print(f"Scraping page {current_page}...")
        
        # Find all rows
        rows = driver.find_elements(
            By.XPATH,
            '//tbody[contains(@class, "p-datatable-tbody")]/tr[contains(@class, "ng-star-inserted")]'
        )
        
        if not rows:
            print("No rows found")
            break
        
        print(f"Found {len(rows)} rows on page {current_page}")
        
        # Extract tickers from rows
        for row in rows:
            try:
                ticker_element = row.find_element(
                    By.XPATH,
                    './/div[contains(@class, "scan-for-stocks__company-symbol")]'
                )
                ticker = ticker_element.text.strip()
                tickers.append(ticker)
                print(f"Found ticker: {ticker}")
            except Exception as e:
                print(f"Error extracting ticker from row: {e}")
                continue
        
        # Check for next page
        try:
            next_button = driver.find_element(
                By.XPATH,
                '//button[contains(@class, "p-paginator-next") and contains(@class, "p-paginator-element")]'
            )
            
            if 'p-disabled' in next_button.get_attribute('class'):
                print("Reached last page")
                break
            
            print("Clicking next page...")
            next_button.click()
            time.sleep(2)
            current_page += 1
            
        except NoSuchElementException:
            print("No pagination found")
            break
    
    print(f"✅ Scraped {len(tickers)} ticker symbols")
    return tickers

def save_rule1_list_to_db(tickers):
    """Save Rule1 list tickers to scraper_tasks table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get or create guru for rule1
        cursor.execute("""
            INSERT INTO guru (guru_name, description) 
            VALUES (%s, %s) 
            ON CONFLICT (guru_name) DO NOTHING 
            RETURNING id
        """, ('rule1', 'Rule1 filtered stocks'))
        
        guru_result = cursor.fetchone()
        if guru_result:
            guru_id = guru_result[0]
        else:
            cursor.execute("SELECT id FROM guru WHERE guru_name = %s", ('rule1',))
            guru_id = cursor.fetchone()[0]
        
        for ticker in tickers:
            cursor.execute("""
                INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type, active, scrape_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, guru_id, list_type) 
                DO UPDATE SET 
                    active = TRUE,
                    scrape_status = CASE 
                        WHEN scraper_tasks.list_type = 'rule1_list' THEN 'pending'
                        ELSE scraper_tasks.scrape_status
                    END
            """, (ticker, guru_id, 'rule1_list', 'monthly', True, 'pending'))
        
        conn.commit()
        print(f"✅ Saved {len(tickers)} tickers to database")
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    max_retries = 3
    
    for attempt in range(max_retries):
        driver = None
        try:
            print(f"\n🔄 Attempt {attempt + 1}/{max_retries}")
            
            # Clean up processes
            kill_chrome_processes()
            time.sleep(2)
            
            # Initialize driver
            driver = get_simple_driver(headless=False)
            
            # Test connection
            driver.get("https://google.com")
            print("✅ Browser test successful")
            time.sleep(2)
            
            # Login
            if not simple_rule1_login(driver):
                raise Exception("Login failed")
            
            # Navigate to stock scan
            if not navigate_to_stock_scan(driver):
                raise Exception("Navigation failed")
            
            # Configure scores
            configure_rule_one_scores(driver)
            
            # Apply filter
            apply_filter(driver)
            
            # Scrape tickers
            tickers = scrape_tickers(driver)
            
            if tickers:
                save_rule1_list_to_db(tickers)
                print(f"✅ Successfully completed! Found {len(tickers)} tickers")
                return True
            else:
                print("❌ No tickers found")
                return False
                
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("⏳ Waiting 15 seconds before retry...")
                time.sleep(15)
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            kill_chrome_processes()
    
    print("❌ All attempts failed")
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Script completed successfully")
    else:
        print("\n❌ Script failed")
        exit(1)