#!/usr/bin/env python
"""
Daily scraper service that respects guru_ticker_map structure
"""

from run_sequential_scraping import run_sequential_scraping
from firebase_notifier import FirebaseNotifier
from datetime import datetime

if __name__ == "__main__":
    try:
        run_sequential_scraping()
        FirebaseNotifier.send_notification(
            title="Scraper Complete",
            body="Daily scraper finished successfully!",
            data={"script": "daily_scraper", "timestamp": str(datetime.now())}
        )
    except Exception as e:
        FirebaseNotifier.send_notification(
            title="Scraper Failed",
            body=f"Daily scraper failed: {str(e)}",
            data={"script": "daily_scraper", "error": str(e), "timestamp": str(datetime.now())}
        )