#!/usr/bin/env python
"""
Monthly Ticker Task Scheduler Service
Runs the monthly ticker task on a configurable schedule
"""

import os
import sys
import time
import json
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

class SchedulerService:
    def __init__(self, config_file="api/scheduler_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.running = False
        self.thread = None
        self.next_run = None
        self.last_run = None
        self.status = "stopped"
        
    def load_config(self):
        """Load scheduler configuration"""
        default_config = {
            "enabled": True,
            "schedule_type": "monthly",  # monthly, weekly, daily, custom
            "day_of_month": 1,  # 1-31 for monthly
            "hour": 9,  # 0-23
            "minute": 0,  # 0-59
            "timezone": "local",
            "script_path": "monthly_ticker_task.py",
            "max_retries": 3,
            "retry_delay": 300  # 5 minutes
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
            return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config
    
    def save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def calculate_next_run(self):
        """Calculate the next run time based on schedule"""
        now = datetime.now()
        
        if self.config["schedule_type"] == "monthly":
            # Next month, same day and time
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1)
            else:
                next_month = now.replace(month=now.month + 1)
            
            # Set to configured day, hour, minute
            try:
                next_run = next_month.replace(
                    day=min(self.config["day_of_month"], 28),  # Safe day
                    hour=self.config["hour"],
                    minute=self.config["minute"],
                    second=0,
                    microsecond=0
                )
            except ValueError:
                # Handle invalid day (e.g., Feb 30)
                next_run = next_month.replace(
                    day=1,
                    hour=self.config["hour"],
                    minute=self.config["minute"],
                    second=0,
                    microsecond=0
                )
        
        elif self.config["schedule_type"] == "weekly":
            # Next week, same time
            next_run = now + timedelta(weeks=1)
            next_run = next_run.replace(
                hour=self.config["hour"],
                minute=self.config["minute"],
                second=0,
                microsecond=0
            )
        
        elif self.config["schedule_type"] == "daily":
            # Tomorrow, same time
            next_run = now + timedelta(days=1)
            next_run = next_run.replace(
                hour=self.config["hour"],
                minute=self.config["minute"],
                second=0,
                microsecond=0
            )
        
        else:  # custom - run immediately for testing
            next_run = now + timedelta(minutes=1)
        
        return next_run
    
    def run_task(self):
        """Execute the monthly ticker task"""
        script_path = self.config["script_path"]
        max_retries = self.config["max_retries"]
        retry_delay = self.config["retry_delay"]
        
        for attempt in range(max_retries):
            try:
                print(f"Running task attempt {attempt + 1}/{max_retries}")
                self.status = f"running (attempt {attempt + 1})"
                
                # Run the script
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=3600  # 1 hour timeout
                )
                
                if result.returncode == 0:
                    print("Task completed successfully")
                    self.status = "completed"
                    self.last_run = datetime.now()
                    return True
                else:
                    print(f"Task failed with code {result.returncode}")
                    print(f"Error: {result.stderr}")
                    
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    
            except subprocess.TimeoutExpired:
                print(f"Task timed out on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                print(f"Error running task: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        print("All retry attempts failed")
        self.status = "failed"
        return False
    
    def scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                if not self.config["enabled"]:
                    time.sleep(60)  # Check every minute
                    continue
                
                now = datetime.now()
                
                if self.next_run is None:
                    self.next_run = self.calculate_next_run()
                    print(f"Next run scheduled for: {self.next_run}")
                
                if now >= self.next_run:
                    print(f"Starting scheduled task at {now}")
                    success = self.run_task()
                    
                    # Schedule next run
                    self.next_run = self.calculate_next_run()
                    print(f"Next run scheduled for: {self.next_run}")
                    
                    if success:
                        self.status = "waiting"
                    else:
                        self.status = "failed"
                else:
                    self.status = "waiting"
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def start(self):
        """Start the scheduler service"""
        if self.running:
            return False
        
        self.running = True
        self.status = "starting"
        self.thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.thread.start()
        self.status = "waiting"
        return True
    
    def stop(self):
        """Stop the scheduler service"""
        if not self.running:
            return False
        
        self.running = False
        self.status = "stopping"
        if self.thread:
            self.thread.join(timeout=5)
        self.status = "stopped"
        return True
    
    def run_now(self):
        """Run the task immediately"""
        if self.status == "running":
            return False, "Task is already running"
        
        def run_async():
            success = self.run_task()
            if success:
                self.status = "waiting"
            else:
                self.status = "failed"
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        return True, "Task started"
    
    def get_status(self):
        """Get current service status"""
        return {
            "running": self.running,
            "status": self.status,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "config": self.config
        }
    
    def update_config(self, new_config):
        """Update configuration"""
        try:
            self.config.update(new_config)
            self.save_config()
            
            # Recalculate next run if schedule changed
            if any(key in new_config for key in ["schedule_type", "day_of_month", "hour", "minute"]):
                self.next_run = self.calculate_next_run()
            
            return True, "Configuration updated"
        except Exception as e:
            return False, f"Error updating config: {e}"

# Global service instance
scheduler_service = SchedulerService()