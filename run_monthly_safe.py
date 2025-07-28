#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Safe wrapper for monthly ticker task with proper encoding handling
"""

import sys
import os

# Fix encoding issues on Windows BEFORE importing anything else
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set environment variable to ensure subprocess uses UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Now import and run the monthly task
from monthly_ticker_task import main

if __name__ == "__main__":
    print("Starting Monthly Ticker Task with encoding fixes...")
    try:
        success = main()
        if success:
            print("Monthly Ticker Task completed successfully!")
        else:
            print("Monthly Ticker Task failed!")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running Monthly Ticker Task: {e}")
        sys.exit(1)