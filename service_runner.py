#!/usr/bin/env python
"""
Standalone service runner for the monthly ticker task scheduler
Run this to start the scheduler service without the API
"""

import os
import sys
import signal
import time

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from api.scheduler_service import scheduler_service

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutting down scheduler service...")
    scheduler_service.stop()
    sys.exit(0)

def main():
    """Main service runner"""
    print("Monthly Ticker Task Scheduler Service")
    print("=====================================")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the scheduler
    print("Starting scheduler service...")
    success = scheduler_service.start()
    
    if not success:
        print("Failed to start scheduler service")
        return 1
    
    print("Scheduler service started successfully")
    print("Press Ctrl+C to stop the service")
    
    # Keep the service running
    try:
        while True:
            status = scheduler_service.get_status()
            print(f"Status: {status['status']} | Next run: {status['next_run'] or 'Not scheduled'}")
            time.sleep(60)  # Print status every minute
    except KeyboardInterrupt:
        print("\nReceived shutdown signal")
    finally:
        scheduler_service.stop()
        print("Scheduler service stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())