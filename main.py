#!/usr/bin/env python
"""Main orchestrator service that runs all scraping services in sequence"""

import subprocess
import sys

def run_service(service_name):
    """Run a systemd service and return success status"""
    try:
        result = subprocess.run(['systemctl', 'start', service_name], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {service_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {service_name} failed: {e.stderr}")
        return False

def main():
    """Run all services in sequence"""
    services = [
        'month-rule.service',
        'stockscores-to-db.service', 
        'rule1-guru-to-db.service',
        'dan-watchlist-to-db.service',
        'rule1-list-to-db.service',
        'run-sequential-scraping.service'
    ]
    
    print("Starting main scraper orchestrator...")
    
    success_count = 0
    for service in services:
        print(f"\nRunning {service}...")
        if run_service(service):
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(services)} services successful")
    
    if success_count == len(services):
        print("✅ All services completed successfully")
        sys.exit(0)
    else:
        print("❌ Some services failed")
        sys.exit(1)

if __name__ == "__main__":
    main()