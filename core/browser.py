import os
import sys
from dotenv import load_dotenv
import undetected_chromedriver as uc

load_dotenv()

def get_driver(headless=True):
    """
    Initialize and return an undetected Chrome browser instance.
    Uses environment variables for configuration.
    
    Args:
        headless (bool): Whether to run Chrome in headless mode (default: True for Ubuntu VPS)
    
    Returns:
        uc.Chrome: Configured undetected Chrome browser instance
    """
    try:
        print("Initializing undetected Chrome browser...")
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        if headless:
            # Use the appropriate headless mode based on Chrome version
            options.add_argument("--headless")
            options.add_argument("--headless=new")  # For newer Chrome versions
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        # options.add_argument("--single-process")  # Removed - causes crashes
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-login-animations")
        options.add_argument("--disable-motion-blur")
        options.add_argument("--disable-translate")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-crash-reporter")
        options.add_argument("--disable-in-process-stack-traces")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")

        # Use Chrome binary path from .env (only if it's a valid string)
        binary_path = os.getenv("CHROME_BINARY_PATH")
        if binary_path and isinstance(binary_path, str) and binary_path.strip():
            options.binary_location = binary_path.strip()

        # Get driver path and version from .env
        driver_path = os.getenv("CHROME_DRIVER_PATH")
        chrome_version = int(os.getenv("CHROME_VERSION", "138"))

        if driver_path and isinstance(driver_path, str) and driver_path.strip():
            driver = uc.Chrome(driver_executable_path=driver_path.strip(), options=options, version_main=chrome_version)
        else:
            driver = uc.Chrome(options=options, version_main=chrome_version)

        print("Chrome session started successfully")
        print("Executable path:", driver.capabilities.get("chrome", {}).get("chromedriverVersion", "Unknown"))
        print("Browser version:", driver.capabilities.get("browserVersion", "Unknown"))

        return driver

    except Exception as e:
        print(f"Failed to initialize Chrome browser: {e}")
        print("Please ensure Chrome and ChromeDriver are properly installed and configured.")
        sys.exit(1)
