#!/usr/bin/env python
import subprocess
import os

def fix_file_limits():
    """Fix file descriptor limits and clean up processes"""
    
    # Kill any hanging Chrome processes
    subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
    subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True)
    
    # Clean up temp directories
    subprocess.run(['rm', '-rf', '/tmp/chrome_*'], shell=True, capture_output=True)
    
    # Increase file descriptor limits
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
        print("✅ File descriptor limit increased to 65536")
    except:
        print("⚠️ Could not increase file descriptor limit")
    
    print("✅ Cleanup complete")

if __name__ == "__main__":
    fix_file_limits()