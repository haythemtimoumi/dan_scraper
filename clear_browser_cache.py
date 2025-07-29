#!/usr/bin/env python
"""
Script to clear browser cache and reset browser state.
Run this when experiencing connection issues or browser session problems.
"""

import os
import shutil
import glob
from pathlib import Path

def clear_chrome_cache():
    """Clear Chrome browser cache and temporary files"""
    print("🧹 Clearing Chrome browser cache...")
    
    # Common Chrome cache directories
    cache_paths = [
        "~/.cache/google-chrome",
        "~/.config/google-chrome",
        "/tmp/chrome_*",
        "/tmp/.com.google.Chrome.*",
        "~/.local/share/undetected_chromedriver"
    ]
    
    cleared_count = 0
    
    for cache_path in cache_paths:
        expanded_path = os.path.expanduser(cache_path)
        
        # Handle glob patterns
        if '*' in expanded_path:
            matching_paths = glob.glob(expanded_path)
            for path in matching_paths:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                        print(f"✅ Removed directory: {path}")
                        cleared_count += 1
                    elif os.path.isfile(path):
                        os.remove(path)
                        print(f"✅ Removed file: {path}")
                        cleared_count += 1
                except Exception as e:
                    print(f"⚠️ Could not remove {path}: {e}")
        else:
            # Handle regular paths
            try:
                if os.path.exists(expanded_path):
                    if os.path.isdir(expanded_path):
                        shutil.rmtree(expanded_path)
                        print(f"✅ Removed directory: {expanded_path}")
                        cleared_count += 1
                    elif os.path.isfile(expanded_path):
                        os.remove(expanded_path)
                        print(f"✅ Removed file: {expanded_path}")
                        cleared_count += 1
            except Exception as e:
                print(f"⚠️ Could not remove {expanded_path}: {e}")
    
    print(f"🎉 Cache clearing complete! Removed {cleared_count} items.")

def kill_chrome_processes():
    """Kill any remaining Chrome processes"""
    print("🔪 Killing Chrome processes...")
    
    try:
        import psutil
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.kill()
                    print(f"✅ Killed Chrome process: {proc.info['pid']}")
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        print(f"🎉 Killed {killed_count} Chrome processes.")
        
    except ImportError:
        print("⚠️ psutil not available, using system commands...")
        os.system("pkill -f chrome")
        print("✅ Attempted to kill Chrome processes using pkill")

if __name__ == "__main__":
    print("🚀 Starting browser cache cleanup...")
    kill_chrome_processes()
    clear_chrome_cache()
    print("✨ Browser cleanup complete! You can now run your scraper again.")