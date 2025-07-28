#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Monthly Ticker Task Runner
Runs all ticker collection and scraping tasks in sequence
"""

import subprocess
import sys
import time

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_script(script_name, continue_on_error=False):
    """Run a Python script and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {script_name}")
    print(f"{'='*50}")
    
    try:
        # Use shell=True on Windows to avoid encoding issues
        cmd = f'python "{script_name}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                              encoding='utf-8', errors='replace', timeout=300)
        
        if result.returncode == 0:
            print(f"✓ {script_name} completed successfully")
            if result.stdout:
                print("Output:", result.stdout)
            return True
        else:
            print(f"✗ {script_name} failed with error code {result.returncode}")
            if result.stdout:
                print("Output:", result.stdout)
            if result.stderr:
                print("Error:", result.stderr)
            if continue_on_error:
                print(f"⚠️ Continuing despite error in {script_name}")
                return True
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {script_name} timed out after 5 minutes")
        if continue_on_error:
            print(f"⚠️ Continuing despite timeout in {script_name}")
            return True
        return False
    except Exception as e:
        print(f"✗ {script_name} failed with exception: {e}")
        if continue_on_error:
            print(f"⚠️ Continuing despite error in {script_name}")
            return True
        return False

def main():
    """Run all monthly ticker tasks in sequence"""
    print("Starting Monthly Ticker Task Pipeline")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Phase 1: Data collection scripts
    phase1_scripts = [
        "month_rule.py",
        "stockscores_to_db.py", 
        "rule1_guru_to_db.py",
        "dan_watchlist_to_db.py",
        "rule1_list_to_db.py"
    ]
    
    print("\n🔄 PHASE 1: Data Collection")
    for script in phase1_scripts:
        # Allow rule1_guru_to_db.py to continue on error due to encoding issues
        continue_on_error = script == "rule1_guru_to_db.py"
        success = run_script(script, continue_on_error)
        if not success:
            print(f"❌ Pipeline failed at {script}")
            return False
        time.sleep(2)  # Brief pause between scripts
    
    # Phase 2: State change
    print("\n🔄 PHASE 2: State Change")
    success = run_script("scraper_state_change.py")
    if not success:
        print("❌ Pipeline failed at scraper_state_change.py")
        return False
    
    # Phase 3: Sequential scraping
    print("\n🔄 PHASE 3: Sequential Scraping")
    success = run_script("run_sequential_scraping.py")
    if not success:
        print("❌ Pipeline failed at run_sequential_scraping.py")
        return False
    
    print(f"\n✅ Monthly Ticker Task Pipeline completed successfully!")
    print(f"Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)