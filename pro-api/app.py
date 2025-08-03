#!/usr/bin/env python
"""API for managing scraper services at stock-ticker.dev"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys

# Add the parent directory to the path to import config
sys.path.append('/root/dan_scraper')

app = Flask(__name__)

# Configure CORS for the new domain
CORS(app, origins=[
    'https://stock-ticker.dev',
    'https://www.stock-ticker.dev',
    'https://www.mytickerlist.com',
    'https://mytickerlist.com',
    'http://localhost:3000',
    'http://localhost:8000'
])

SERVICES = [
    'month-rule.service',
    'stockscores-to-db.service', 
    'rule1-guru-to-db.service',
    'dan-watchlist-to-db.service',
    'rule1-list-to-db.service',
    'run-sequential-scraping.service',
    'main-scraper.service',
    'dan-scraper-daily.service'
]

@app.route('/run-service', methods=['POST'])
def run_service():
    """Run a specific service"""
    data = request.get_json()
    service_name = data.get('service')
    
    if service_name not in SERVICES:
        return jsonify({'error': 'Invalid service name'}), 400
    
    try:
        # For main-scraper.service, start the timer instead
        if service_name == 'main-scraper.service':
            subprocess.Popen(['systemctl', 'start', 'main-scraper.timer'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({'success': True, 'message': 'Main scraper timer started for scheduled execution'})
        else:
            # Start other services directly
            subprocess.Popen(['systemctl', 'start', service_name], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({'success': True, 'message': f'{service_name} start command sent'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to start {service_name}: {str(e)}'}), 500



@app.route('/', methods=['GET'])
def root():
    """API information"""
    return jsonify({
        'name': 'Stock Ticker Scraper API',
        'domain': 'stock-ticker.dev',
        'version': '1.0.0',
        'endpoints': {
            'services': '/services',
            'run_service': '/run-service',
            'update_timer': '/update-timer',
            'start_main_scraper': '/start-main-scraper',
            'stop_main_scraper': '/stop-main-scraper',
            'monthly_scraper_status': '/monthly-scraper-status',
            'start_daily_service': '/start-daily-service',
            'stop_daily_service': '/stop-daily-service',
            'config': '/config',
            'update_timer': '/update-timer',
            'status': '/status'
        }
    })

@app.route('/services', methods=['GET'])
def list_services():
    """List available services"""
    return jsonify({'services': SERVICES})

@app.route('/stop-main-scraper', methods=['POST'])
def stop_main_scraper():
    """Stop the main scraper timer to prevent future scheduled launches"""
    try:
        # Only stop the timer to prevent future scheduled executions
        subprocess.run(['systemctl', 'stop', 'main-scraper.timer'], 
                      capture_output=True, text=True)
        
        return jsonify({
            'success': True, 
            'message': 'Main scraper timer stopped - no future scheduled launches'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to stop main scraper timer: {str(e)}'}), 500

@app.route('/monthly-scraper-status', methods=['GET'])
def monthly_scraper_status():
    """Get current state of monthly scraper"""
    try:
        # Check month-rule service status
        result = subprocess.run(['systemctl', 'is-active', 'month-rule.service'], 
                              capture_output=True, text=True)
        service_status = result.stdout.strip()
        
        # Get last run time
        result = subprocess.run(['systemctl', 'show', 'month-rule.service', '--property=ActiveEnterTimestamp'], 
                              capture_output=True, text=True)
        last_run = result.stdout.strip().replace('ActiveEnterTimestamp=', '') if result.stdout else 'Never'
        
        # Check database for scraper_tasks status
        import psycopg2
        from config.settings import DB_CONFIG
        
        db_status = {}
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Get total tickers count
            cursor.execute("SELECT COUNT(*) FROM scraper_tasks")
            total_tickers = cursor.fetchone()[0]
            
            # Get active tickers count
            cursor.execute("SELECT COUNT(*) FROM scraper_tasks WHERE active = true")
            active_tickers = cursor.fetchone()[0]
            
            # Get status distribution
            cursor.execute("""
                SELECT scrape_status, COUNT(*) 
                FROM scraper_tasks 
                GROUP BY scrape_status
            """)
            status_counts = dict(cursor.fetchall())
            
            db_status = {
                'total_tickers': total_tickers,
                'active_tickers': active_tickers,
                'inactive_tickers': total_tickers - active_tickers,
                'status_distribution': status_counts
            }
            
            cursor.close()
            conn.close()
            
        except Exception as db_error:
            db_status = {'error': f'Database connection failed: {str(db_error)}'}
        
        return jsonify({
            'service_status': service_status,
            'last_run': last_run,
            'database_status': db_status
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get monthly scraper status: {str(e)}'}), 500

@app.route('/start-daily-service', methods=['POST'])
def start_daily_service():
    """Start the daily scraper service"""
    try:
        subprocess.Popen(['systemctl', 'start', 'dan-scraper-daily.service'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({
            'success': True, 
            'message': 'Daily scraper service start command sent'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start daily service: {str(e)}'}), 500

@app.route('/stop-daily-service', methods=['POST'])
def stop_daily_service():
    """Stop the daily scraper service"""
    try:
        subprocess.Popen(['systemctl', 'stop', 'dan-scraper-daily.service'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({
            'success': True, 
            'message': 'Daily scraper service stop command sent'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to stop daily service: {str(e)}'}), 500

@app.route('/config', methods=['POST'])
def update_config():
    """Update which script should run (run_sequential_scraping or daily_process)"""
    data = request.get_json()
    script = data.get('script')
    
    if script not in ['run_sequential_scraping', 'daily_process']:
        return jsonify({'error': 'Invalid script. Must be run_sequential_scraping or daily_process'}), 400
    
    try:
        import json
        config = {'script': script}
        with open('/root/dan_scraper/pro-api/scraper_config.json', 'w') as f:
            json.dump(config, f)
        
        return jsonify({
            'success': True,
            'message': f'Configuration updated to run {script}'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to update config: {str(e)}'}), 500

@app.route('/update-timer', methods=['POST'])
def update_main_timer():
    """Update main scraper timer schedule"""
    data = request.get_json()
    schedule = data.get('schedule')
    
    if not schedule:
        return jsonify({'error': 'Schedule is required'}), 400
    
    timer_content = f"""[Unit]
Description=Daily Scraper Timer
Requires=daily-scraper.service

[Timer]
OnCalendar={schedule}

[Install]
WantedBy=timers.target"""
    
    try:
        subprocess.run(['systemctl', 'stop', 'daily-scraper.timer'], check=False)
        
        with open('/root/dan_scraper/pro-api/daily-scraper.timer', 'w') as f:
            f.write(timer_content)
        
        subprocess.run(['cp', '/root/dan_scraper/pro-api/daily-scraper.timer', '/etc/systemd/system/'], check=True)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'start', 'daily-scraper.timer'], check=True)
        
        return jsonify({'success': True, 'message': f'Timer updated to: {schedule}'})
    except Exception as e:
        return jsonify({'error': f'Failed to update timer: {str(e)}'}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get main scraper status"""
    try:
        # Check service status
        result = subprocess.run(['systemctl', 'is-active', 'daily-scraper.service'], 
                              capture_output=True, text=True)
        service_status = result.stdout.strip()
        
        # Check timer status
        result = subprocess.run(['systemctl', 'is-active', 'daily-scraper.timer'], 
                              capture_output=True, text=True)
        timer_status = result.stdout.strip()
        
        # Get last run time
        result = subprocess.run(['systemctl', 'show', 'daily-scraper.service', '--property=ActiveEnterTimestamp'], 
                              capture_output=True, text=True)
        last_run = result.stdout.strip().replace('ActiveEnterTimestamp=', '') if result.stdout else 'Never'
        
        # Get current config
        import json
        try:
            with open('/root/dan_scraper/pro-api/scraper_config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {'script': 'run_sequential_scraping'}
        
        return jsonify({
            'service_status': service_status,
            'timer_status': timer_status,
            'last_run': last_run,
            'current_script': config.get('script', 'run_sequential_scraping')
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)