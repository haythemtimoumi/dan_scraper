from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import psutil
import psycopg2
import subprocess
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_CONFIG

app = Flask(__name__)
CORS(app)

TICKER_FILE_PATH = "../config/tickers_rule1.txt"
STATUS_FILE_PATH = "../scraper_status.json"

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def is_scraper_running():
    """Check if dan_scraper.service is running"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'dan_scraper.service'], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def get_last_scrape_time():
    """Get the last scrape time from systemctl service status"""
    try:
        result = subprocess.run(['systemctl', 'show', 'dan_scraper.service', '--property=ExecMainExitTimestamp'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            timestamp_line = result.stdout.strip()
            if '=' in timestamp_line:
                timestamp_str = timestamp_line.split('=', 1)[1].strip()
                if timestamp_str and timestamp_str != 'n/a':
                    # Parse systemd timestamp format
                    return datetime.strptime(timestamp_str, '%a %Y-%m-%d %H:%M:%S %Z')
        return None
    except Exception as e:
        print(f"Error getting last scrape time: {e}")
        return None

def calculate_next_run_time():
    """Calculate time until next scrape (runs daily at 02:00 UTC)"""
    now = datetime.utcnow()
    
    # Next run is at 02:00 UTC today or tomorrow
    today_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
    
    if now < today_2am:
        # Next run is today at 02:00
        next_run = today_2am
    else:
        # Next run is tomorrow at 02:00
        next_run = today_2am + timedelta(days=1)
    
    diff = next_run - now
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    return round(diff.total_seconds() / 3600, 1), f"{hours}h:{minutes}m"

@app.route('/scraper-status', methods=['GET'])
def get_scraper_status():
    """Get current scraper status and timing information"""
    try:
        # Check if scraper is currently running
        is_running = is_scraper_running()
        
        # Get last run time
        last_run = get_last_scrape_time()
        last_run_str = last_run.strftime('%Y-%m-%d %H:%M:%S') if last_run else None
        
        # Calculate next run time
        next_run_hours, next_run_formatted = calculate_next_run_time()
        
        # Next scheduled run is at 02:00 UTC today or tomorrow
        now = datetime.utcnow()
        today_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
        
        if now < today_2am:
            next_run_time = today_2am.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tomorrow_2am = today_2am + timedelta(days=1)
            next_run_time = tomorrow_2am.strftime('%Y-%m-%d %H:%M:%S')
        
        # Determine status
        if is_running:
            status = "running"
        elif next_run_hours <= 0:
            status = "ready"  # Should run soon
        else:
            status = "idle"
        
        return jsonify({
            "can_update_tickers": not is_running,
            "is_running": is_running,
            "last_run": last_run_str,
            "next_run_in_hours_minutes": next_run_formatted,
            "next_scheduled_run": next_run_time,
            "status": status
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-tickers', methods=['POST'])
def update_tickers():
    """Update ticker list if scraper is not running"""
    try:
        # Check if scraper is running
        if is_scraper_running():
            return jsonify({
                "error": "Cannot update tickers while scraper is running",
                "scraper_status": "running",
                "message": "Please wait for scraper to finish before updating tickers"
            }), 409
        
        # Get JSON data from request
        data = request.json
        
        # Validate request
        if not data or 'tickers' not in data or not isinstance(data['tickers'], list):
            return jsonify({"error": "Invalid request. Expected JSON with 'tickers' array"}), 400
        
        # Get and clean tickers
        tickers = [str(ticker).strip().upper() for ticker in data['tickers'] if ticker]
        
        if not tickers:
            return jsonify({"error": "No valid ticker symbols provided"}), 400
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(TICKER_FILE_PATH), exist_ok=True)
        
        # Write the new tickers to the file
        with open(TICKER_FILE_PATH, 'w') as f:
            for ticker in tickers:
                f.write(f"{ticker}\n")
        
        # Get scraper status for response
        next_run_hours, _ = calculate_next_run_time()
        
        return jsonify({
            "success": True,
            "message": f"Successfully updated {len(tickers)} tickers",
            "tickers_updated": len(tickers),
            "sample_tickers": tickers[:5] + (["..."] if len(tickers) > 5 else []),
            "scraper_status": "idle",
            "next_run_in_hours": next_run_hours
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-tickers', methods=['GET'])
def get_current_tickers():
    """Get current ticker list"""
    try:
        if not os.path.exists(TICKER_FILE_PATH):
            return jsonify({"tickers": []})
        
        with open(TICKER_FILE_PATH, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
        
        return jsonify({
            "tickers": tickers,
            "count": len(tickers)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Ticker Management API...")
    print("📡 API will be available at http://localhost:5000")
    print("📋 Endpoints:")
    print("   GET  /scraper-status  - Get scraper status and timing")
    print("   POST /update-tickers  - Update ticker list")
    print("   GET  /get-tickers     - Get current tickers")
    app.run(host='0.0.0.0', port=5000, debug=False)