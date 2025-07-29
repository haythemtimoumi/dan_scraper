import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

def get_firefox_driver(headless=True):
    """Get a Firefox driver as alternative to Chrome"""
    
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    # Basic options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        print("Firefox driver initialized successfully")
        return driver
    except Exception as e:
        print(f"Failed to initialize Firefox: {e}")
        raise e