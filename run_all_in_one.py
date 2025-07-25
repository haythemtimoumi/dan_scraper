#!/usr/bin/env python
# Script to run the entire process in one command

import os
import time
import argparse
from dotenv import load_dotenv
from scrapers.rule1_scraper import Rule1Scraper
from scrapers.scores_scraper import TickerSearcher
from scrapers.stockscores_scraper import StockScoresScraper
from scrapers.guru_scraper import GuruScraper
from scrapers.stockscores_login import login_to_stockscores
from utils.source_tracker import save_ticker_source
# Import our new merge_and_save function instead of the old one
try:
    from merge_and_save import merge_and_save
except ImportError:
    from merge_to_database import merge_and_save_to_db

# Load environment variables
load_dotenv()

def clear_csv_files():
    """Clear old CSV files before new scraping run (keeps manual list)"""
    files_to_clear = [
        "ticker_data.csv",
        "stockscores_data.csv", 
        "guru_data.csv",
        "guru_tickers.txt",
        "stock_list_tickers.txt",
        "scraped_tickers.txt",
        "combined_tickers.txt",
        "merged_stock_data.csv"
    ]
    
    print("🧹 Clearing old CSV files...")
    
    for file_path in files_to_clear:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Deleted {file_path}")
        except Exception as e:
            print(f"⚠️ Error deleting {file_path}: {e}")
    
    # Keep config/tickers_rule1.txt (manual list)
    manual_list = "config/tickers_rule1.txt"
    if os.path.exists(manual_list):
        print(f"✅ Kept manual list: {manual_list}")
    
    print("🎉 CSV cleanup complete!")

def run_all_in_one(auto_verify=True, max_retries=3):
    """
    Run the entire process from scraping to database saving in one command
    
    Args:
        auto_verify (bool): Whether to automatically verify email code
        max_retries (int): Maximum number of retries
    """
    print("🚀 Starting complete stock data pipeline...")
    
    # Clear old CSV files first (like run_clean_pipeline.py)
    clear_csv_files()
    
    for attempt in range(max_retries):
        scraper = None
        try:
            print(f"🔄 Scraping attempt {attempt + 1}/{max_retries}")
            
            # Step 0: Run StockScores login and scrape tickers
            print("\n📋 STEP 0: Run StockScores login and scrape tickers")
            try:
                stockscores_driver = login_to_stockscores(headless=True)  # Use headless mode for Ubuntu VPS
                if stockscores_driver:
                    print("✅ StockScores login and ticker scraping completed")
                    stockscores_driver.quit()
                    # Wait for browser to fully close
                    time.sleep(3)
                else:
                    print("⚠️ StockScores login failed, continuing without stock_list tickers")
            except Exception as stockscores_error:
                print(f"⚠️ Error during StockScores login: {stockscores_error}")
                print("Creating empty stock_list_tickers.txt file to avoid errors")
                with open("stock_list_tickers.txt", "w") as f:
                    pass
            
            # Create Rule1Scraper instance after StockScores is completely done
            scraper = Rule1Scraper()
            
            try:
                # Step 1: Login to Rule1Toolbox
                print("\n📋 STEP 1: Login to Rule1Toolbox")
                login_success = scraper.login(auto_verify=auto_verify)
                if not login_success:
                    print("❌ Login failed.")
                    if attempt < max_retries - 1:
                        print("🔄 Retrying with a new browser instance...")
                        continue
                    else:
                        print("❌ All login attempts failed. Exiting.")
                        return
                
                # Step 2: Navigate to the Stock Scan page
                print("\n📋 STEP 2: Navigate to Stock Scan page")
                nav_success = scraper.navigate_to_stock_scan()
                if not nav_success:
                    print("❌ Navigation to Stock Scan page failed.")
                    if attempt < max_retries - 1:
                        print("🔄 Retrying with a new browser instance...")
                        continue
                    else:
                        print("❌ All navigation attempts failed. Exiting.")
                        return
                    
                # Step 3: Configure Rule One Scores section
                print("\n📋 STEP 3: Configure Rule One Scores")
                config_success = scraper.configure_rule_one_scores()
                if not config_success:
                    print("⚠️ Configuration of Rule One Scores section failed. Continuing anyway...")
                
                # Step 4: Apply filter and scrape ticker symbols
                print("\n📋 STEP 4: Apply filter and scrape tickers")
                filter_success = scraper.apply_filter()
                if not filter_success:
                    print("⚠️ There was an issue applying the filter, but continuing anyway")
                
                print("🔍 Scraping ticker symbols...")
                tickers = scraper.scrape_only_tickers()
                
                if tickers:
                    print(f"✅ Successfully scraped {len(tickers)} ticker symbols")
                    
                    # Save tickers to a file
                    save_path = "scraped_tickers.txt"
                    with open(save_path, 'w') as f:
                        for ticker in tickers:
                            f.write(f"{ticker}\n")
                            # Mark as Rule1 source
                            save_ticker_source(ticker, 'rule1')
                    print(f"✅ Ticker symbols saved to {save_path}")
                else:
                    print("⚠️ No ticker symbols were scraped in this attempt")
                    if attempt < max_retries - 1:
                        print("🔄 Retrying with a new browser instance...")
                        continue
                    else:
                        print("❌ All scraping attempts failed. No ticker symbols were scraped.")
                        # Create an empty file to avoid errors
                        with open("scraped_tickers.txt", 'w') as f:
                            pass
                        print("⚠️ Created empty scraped_tickers.txt file")
                        return
                
                # Step 5.5: Run guru scraper
                print("\n📋 STEP 5.5: Run guru scraper")
                guru_scraper = GuruScraper(driver=scraper.driver)
                try:
                    guru_scraper.run()
                    print("✅ Guru scraping completed")
                except Exception as guru_error:
                    print(f"❌ Error during guru scraping: {guru_error}")
                finally:
                    guru_scraper.close()
                
                # Step 6: Run ticker search
                print("\n📋 STEP 6: Run ticker search")
                searcher = TickerSearcher(driver=scraper.driver)
                try:
                    # The login check will detect we're already logged in
                    if searcher.login(auto_verify=auto_verify):
                        searcher.combine_and_search_tickers()
                    else:
                        print("❌ Failed to login for ticker search")
                except Exception as search_error:
                    print(f"❌ Error during ticker search: {search_error}")
                
                # Close the browser before moving to StockScores
                try:
                    scraper.close()
                    print("✅ Browser closed successfully")
                except Exception as close_error:
                    print(f"⚠️ Error closing browser: {close_error}")
                
                # Step 7: Run StockScores scraper
                print("\n📋 STEP 7: Run StockScores scraper")
                stockscores_scraper = StockScoresScraper(input_file="combined_tickers.txt")
                try:
                    stockscores_scraper.run()
                except Exception as stockscores_error:
                    print(f"❌ Error during StockScores scraping: {stockscores_error}")
                finally:
                    stockscores_scraper.close()
                
                # Step 7.5: Fetch current stock prices
                print("\n📋 STEP 7.5: Fetch current stock prices")
                try:
                    from simple_price_fetcher import fetch_all_prices
                    fetch_all_prices()
                    print("✅ Stock prices fetched successfully")
                except Exception as price_error:
                    print(f"❌ Error fetching stock prices: {price_error}")
                
                # Step 8: Save to database
                print("\n📋 STEP 8: Save to database")
                try:
                    # Try to use our new merge_and_save function
                    merge_and_save()
                    print("✅ Successfully saved data to database")
                except NameError:
                    # Fall back to the old function if the new one isn't available
                    success = merge_and_save_to_db()
                    if success:
                        print("✅ Successfully saved data to database")
                    else:
                        print("❌ Failed to save data to database")
                
                # Step 9: Upload CSV files to S3
                print("\n📋 STEP 9: Upload CSV files to S3")
                try:
                    from upload_daily_csvs import upload_daily_files
                    uploaded_files = upload_daily_files()
                    if uploaded_files:
                        print(f"✅ Successfully uploaded {len(uploaded_files)} files to S3")
                    else:
                        print("⚠️ No files were uploaded to S3")
                except Exception as s3_error:
                    print(f"❌ Error uploading to S3: {s3_error}")
                
                print("\n🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
                print(f"📊 Final ticker sources used:")
                print(f"   - StockScores stock list: stock_list_tickers.txt")
                print(f"   - Rule1 scraped tickers: scraped_tickers.txt")
                print(f"   - Guru portfolio tickers: guru_tickers.txt")
                print(f"   - Manual tickers: config/tickers_rule1.txt")
                return  # Success, exit the retry loop
                    
            except Exception as e:
                print(f"❌ Error during process: {e}")
                # Make sure to close the browser if there's an error
                try:
                    if scraper:
                        scraper.close()
                except:
                    pass
                
                if attempt < max_retries - 1:
                    print("🔄 Retrying with a new browser instance...")
                    time.sleep(5)
                else:
                    print("❌ All attempts failed.")
                    return
                    
        except Exception as e:
            print(f"❌ Error during attempt {attempt + 1}: {e}")
            # Make sure to close the browser if there's an error
            try:
                if scraper:
                    scraper.close()
            except:
                pass
            if attempt < max_retries - 1:
                print("🔄 Retrying...")
                time.sleep(5)
            else:
                print("❌ All attempts failed.")
                return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the entire stock data pipeline in one command")
    parser.add_argument("--manual-verify", action="store_true",
                        help="Manually verify email code instead of automatic verification")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Maximum number of retries for the entire process (default: 3)")
    
    args = parser.parse_args()
    
    run_all_in_one(
        auto_verify=not args.manual_verify,
        max_retries=args.max_retries
    )