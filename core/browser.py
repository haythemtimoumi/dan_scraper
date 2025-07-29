import os
import sys
from dotenv import load_dotenv
import undetected_chromedriver as uc

load_dotenv()

def get_driver(headless=False, clear_cache=False):
    """
    Initialize and return an undetected Chrome browser instance.
    Uses environment variables for configuration.
    
    Args:
        headless (bool): Whether to run Chrome in headless mode (default: True for Ubuntu VPS)
    
    Returns:
        uc.Chrome: Configured undetected Chrome browser instance
    """
    try:
        if clear_cache:
            print("Clearing browser cache...")
            import subprocess
            import shutil
            import glob
            import time
            
            # Kill all Chrome processes more aggressively
            subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
            time.sleep(2)
            
            # Clear cache directories
            cache_paths = ["~/.cache/google-chrome", "~/.config/google-chrome", "~/.local/share/undetected_chromedriver"]
            for path in cache_paths:
                expanded = os.path.expanduser(path)
                if os.path.exists(expanded):
                    shutil.rmtree(expanded, ignore_errors=True)
            
            # Clear temp files
            for tmp_path in glob.glob("/tmp/chrome_*") + glob.glob("/tmp/.com.google.Chrome.*"):
                shutil.rmtree(tmp_path, ignore_errors=True)
            
            print("Cache cleared successfully")
        
        print("Initializing undetected Chrome browser...")

        # Let undetected-chromedriver handle Chrome binary automatically
        # binary_path = os.getenv("CHROME_BINARY_PATH")
        # if binary_path and isinstance(binary_path, str) and binary_path.strip():
        #     options.binary_location = binary_path.strip()
        #     print(f"Using Chrome binary: {binary_path.strip()}")

        # Get driver path and version from .env
        driver_path = os.getenv("CHROME_DRIVER_PATH")
        chrome_version = int(os.getenv("CHROME_VERSION", "138"))

        # Retry mechanism for browser initialization
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Create fresh options for each attempt
                fresh_options = uc.ChromeOptions()
                fresh_options.add_argument("--no-sandbox")
                fresh_options.add_argument("--disable-dev-shm-usage")
                fresh_options.add_argument("--disable-gpu")
                fresh_options.add_argument("--remote-debugging-port=0")
                fresh_options.add_argument("--disable-extensions")
                fresh_options.add_argument("--window-size=1920,1080")
                fresh_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
                
                if clear_cache:
                    fresh_options.add_argument("--disk-cache-size=0")
                    fresh_options.add_argument("--media-cache-size=0")
                
                if headless:
                    fresh_options.add_argument("--headless=new")
                
                fresh_options.add_argument("--no-first-run")
                fresh_options.add_argument("--disable-popup-blocking")
                fresh_options.add_argument("--log-level=3")
                
                if driver_path and isinstance(driver_path, str) and driver_path.strip():
                    driver = uc.Chrome(driver_executable_path=driver_path.strip(), options=fresh_options, version_main=chrome_version)
                else:
                    driver = uc.Chrome(options=fresh_options, version_main=chrome_version)
                break
            except Exception as retry_error:
                if attempt < max_retries - 1:
                    print(f"Browser initialization attempt {attempt + 1} failed: {retry_error}")
                    print("Retrying in 3 seconds...")
                    import time
                    time.sleep(3)
                    # Clear any remaining processes and ports
                    import subprocess
                    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
                    subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
                    subprocess.run(["fuser", "-k", "9222/tcp"], capture_output=True)
                    subprocess.run(["fuser", "-k", "9223/tcp"], capture_output=True)
                else:
                    raise retry_error

        print("Chrome session started successfully")
        print("Executable path:", driver.capabilities.get("chrome", {}).get("chromedriverVersion", "Unknown"))
        print("Browser version:", driver.capabilities.get("browserVersion", "Unknown"))

        return driver

    except Exception as e:
        print(f"Failed to initialize Chrome browser: {e}")
        print("Please ensure Chrome and ChromeDriver are properly installed and configured.")
        sys.exit(1)
