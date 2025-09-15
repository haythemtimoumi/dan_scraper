#!/usr/bin/env python
"""
Quick fix for Chrome browser initialization issues
"""
import subprocess
import time
import os
import shutil

def fix_chrome_issues():
    """Fix common Chrome initialization issues"""
    
    print("🔧 Fixing Chrome browser issues...")
    
    # 1. Kill all Chrome processes
    print("Killing existing Chrome processes...")
    subprocess.run(["pkill", "-9", "-f", "chrome"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "chromium"], capture_output=True)
    time.sleep(2)
    
    # 2. Clean up temp directories
    print("Cleaning temp directories...")
    temp_patterns = [
        "/tmp/tmp*",
        "/tmp/.com.google.Chrome.*", 
        "/tmp/.org.chromium.Chromium.*",
        "/tmp/chrome_*",
        "/tmp/scoped_dir*"
    ]
    
    for pattern in temp_patterns:
        subprocess.run(f"rm -rf {pattern}", shell=True, capture_output=True)
    
    # 3. Clear Chrome user data
    print("Clearing Chrome user data...")
    chrome_dirs = [
        "~/.cache/google-chrome",
        "~/.config/google-chrome", 
        "~/.local/share/undetected_chromedriver"
    ]
    
    for dir_path in chrome_dirs:
        expanded = os.path.expanduser(dir_path)
        if os.path.exists(expanded):
            shutil.rmtree(expanded, ignore_errors=True)
    
    # 4. Free up ports
    print("Freeing up Chrome debugging ports...")
    for port in [9222, 9223, 9224, 9225]:
        subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
    
    # 5. Check available memory
    print("Checking system resources...")
    result = subprocess.run(["free", "-h"], capture_output=True, text=True)
    print(result.stdout)
    
    print("✅ Chrome fix completed!")

if __name__ == "__main__":
    fix_chrome_issues()