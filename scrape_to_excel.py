#!/usr/bin/env python
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

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
        driver.get("https://www.goldstockdata.com/companies.html")
        time.sleep(3)
        
        # Find email field
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
                break
            except:
                continue
        
        if not email_field:
            return None
        
        email_field.clear()
        email_field.send_keys(os.getenv('GOLDSTOCKDATA_EMAIL'))
        
        password_field = driver.find_element(By.CSS_SELECTOR, 'input.passwd-placeholder')
        password_field.clear()
        password_field.send_keys(os.getenv('GOLDSTOCKDATA_PASSWORD'))
        
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
    company_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
    
    for link in company_links:
        company_name = link.text.strip()
        company_url = link.get_attribute('href')
        
        if company_name and company_url and not company_name.startswith('['):
            if company_url.startswith('/'):
                company_url = 'https://www.goldstockdata.com' + company_url
            
            if '?' not in company_url:
                companies.append({'name': company_name, 'url': company_url})
    
    return companies

def scrape_contact_data(driver):
    """Scrape only category and contact info"""
    try:
        # Get company name
        company_name = ""
        try:
            company_name = driver.find_element(By.CSS_SELECTOR, "div.name h1").text.strip()
            print(f"    Found company name: {company_name}")
        except Exception as e:
            print(f"    Could not find company name: {e}")
        
        # Get category
        category = ""
        try:
            category = driver.find_element(By.CSS_SELECTOR, "#rating-summary tr:first-child td:last-child b").text.strip()
            print(f"    Found category: {category}")
        except Exception as e:
            print(f"    Could not find category: {e}")
            return None
        
        # Get symbol
        symbol = ""
        try:
            main_row = driver.find_element(By.CSS_SELECTOR, "tr.main")
            symbol = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) b").text.strip()
            print(f"    Found symbol: {symbol}")
        except Exception as e:
            print(f"    Could not find symbol: {e}")
        
        # Get company URL
        company_url = ""
        try:
            company_url_element = driver.find_element(By.CSS_SELECTOR, "span.es-nowrap a[href^='http']")
            company_url = company_url_element.get_attribute('href')
            print(f"    Found company URL: {company_url}")
        except Exception as e:
            print(f"    Could not find company URL: {e}")
        
        # Get company email
        company_email = ""
        try:
            company_email_element = driver.find_element(By.CSS_SELECTOR, "span.es-nowrap a[href^='mailto:']")
            company_email = company_email_element.get_attribute('href').replace('mailto:', '')
            print(f"    Found company email: {company_email}")
        except Exception as e:
            print(f"    Could not find company email: {e}")
        
        # Get Development and Production projects
        dev_projects = []
        prod_projects = []
        try:
            property_rows = driver.find_elements(By.CSS_SELECTOR, "#property-snapshot tbody tr")
            for row in property_rows:
                try:
                    stage_cell = row.find_element(By.CSS_SELECTOR, "td:first-child span")
                    stage = stage_cell.get_attribute('title')
                    
                    if stage in ['Development', 'Production']:
                        name_cell = row.find_element(By.CSS_SELECTOR, "td.name b")
                        project_name = name_cell.text.strip()
                        
                        # Get location info
                        location = ""
                        try:
                            location_element = row.find_element(By.CSS_SELECTOR, "td.name .desc i")
                            location = location_element.text.strip()
                        except:
                            pass
                        
                        project_info = f"{project_name} ({location})" if location else project_name
                        
                        if stage == 'Development':
                            dev_projects.append(project_info)
                        elif stage == 'Production':
                            prod_projects.append(project_info)
                except:
                    continue
            
            if dev_projects:
                print(f"    Found Development projects: {', '.join(dev_projects)}")
            if prod_projects:
                print(f"    Found Production projects: {', '.join(prod_projects)}")
                
        except Exception as e:
            print(f"    Could not find property projects: {e}")
        
        return {
            'company_name': company_name,
            'symbol': symbol,
            'category': category,
            'company_url': company_url,
            'company_email': company_email,
            'development_projects': ', '.join(dev_projects) if dev_projects else '',
            'production_projects': ', '.join(prod_projects) if prod_projects else ''
        }
    except Exception as e:
        print(f"    Error scraping data: {e}")
        return None

def scrape_to_excel():
    """Main function to scrape and save to Excel"""
    driver = login_goldstockdata()
    if not driver:
        return
    
    companies = scrape_companies(driver)
    print(f"Found {len(companies)} companies - scraping all")
    
    data = []
    failed_count = 0
    
    try:
        for i, company in enumerate(companies):
            print(f"\nScraping {company['name']} ({i+1}/{len(companies)})")
            print(f"  URL: {company['url']}")
            
            try:
                driver.get(company['url'])
                print(f"  Page loaded, waiting...")
                time.sleep(2)
                
                contact_data = scrape_contact_data(driver)
                if contact_data and contact_data['category']:
                    data.append(contact_data)
                    print(f"  ✅ SUCCESS: {contact_data['company_name']} - {contact_data['category']}")
                    
                    # Save progress every 50 companies
                    if len(data) % 50 == 0:
                        df = pd.DataFrame(data)
                        df.to_excel(f'goldstock_contacts_progress_{len(data)}.xlsx', index=False)
                        print(f"  💾 Progress saved: {len(data)} companies")
                else:
                    failed_count += 1
                    print(f"  ❌ FAILED: No valid data found")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ❌ ERROR processing {company['name']}: {e}")
                continue
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user. Saving {len(data)} companies collected so far...")
    
    # Save final results
    if data:
        df = pd.DataFrame(data)
        df.to_excel('goldstock_contacts.xlsx', index=False)
        print(f"\n📊 Final results saved to goldstock_contacts.xlsx")
        print(f"   ✅ Successful: {len(data)} companies")
        print(f"   ❌ Failed: {failed_count} companies")
        print(f"   📈 Success rate: {len(data)/(len(data)+failed_count)*100:.1f}%")
    else:
        print("\n❌ No data collected")
    
    driver.quit()

if __name__ == "__main__":
    scrape_to_excel()