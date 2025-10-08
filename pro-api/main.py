#!/usr/bin/env python
"""
Main scraper controller that runs either sequential or daily process based on config
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append('/root/dan_scraper')

def run_main():
    """Run the three scripts in sequence"""
    print(f"Starting main scraper at {datetime.now()}")
    
    try:
        # Step 1: Run gold_list_type.py
        print("\n🔸 Step 1: Running gold_list_type.py")
        os.system('cd /root/dan_scraper && python gold_list_type.py')
        
        # Step 2: Run goldstockdata_scraper.py
        print("\n🔸 Step 2: Running goldstockdata_scraper.py")
        os.system('cd /root/dan_scraper && python goldstockdata_scraper.py')
        
        # Step 3: Run test.py
        print("\n🔸 Step 3: Running test.py")
        os.system('cd /root/dan_scraper && python test.py')
        
        print("\n✅ All scripts completed successfully")
        
    except Exception as e:
        print(f"❌ Error running scripts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_main()
    
    # Create daily backup to S3 after scraping
    print("\n🗄️ Creating daily database backup...")
    try:
        from daily_backup_to_s3 import daily_backup_to_s3
        daily_backup_to_s3()
        print("✅ Daily backup completed")
    except Exception as e:
        print(f"❌ Daily backup failed: {e}")