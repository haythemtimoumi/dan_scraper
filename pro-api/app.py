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
    'dan-scraper-daily.service',
    'scrape-active-tickers.service',
    'hourly-scraping.service',
    'scrape-active-tickers-hourly.service',
    'hourly-scraper.service',
    'run-sequential-scraping-manually.service',
    'scrape-active-tickers-manually.service'
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
            'start_active_scraper': '/start-active-scraper',
            'start_hourly_service': '/start-hourly-service',
            'stop_hourly_service': '/stop-hourly-service',
            'hourly_config': '/hourly-config',
            'hourly_status': '/hourly-status',
            'update_hourly_timer': '/update-hourly-timer',
            'run_manual_scraper': '/run-manual-scraper',
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
    
    if script not in ['run_sequential_scraping', 'scrape_all_active_ticker']:
        return jsonify({'error': 'Invalid script. Must be run_sequential_scraping or scrape_all_active_ticker'}), 400
    
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
        
        # Get last run time from both services
        def get_last_run_time(service_name):
            try:
                result = subprocess.run(['systemctl', 'show', service_name, '--property=ExecMainStartTimestamp'], 
                                      capture_output=True, text=True)
                timestamp = result.stdout.strip().replace('ExecMainStartTimestamp=', '')
                return timestamp if timestamp and timestamp != '' and timestamp != 'n/a' else None
            except:
                return None
        
        # Check both services for last run
        sequential_last_run = get_last_run_time('run-sequential-scraping.service')
        active_ticker_last_run = get_last_run_time('scrape-active-tickers.service')
        daily_scraper_last_run = get_last_run_time('daily-scraper.service')
        
        # Find the most recent run
        last_runs = []
        if sequential_last_run:
            last_runs.append(('run-sequential-scraping', sequential_last_run))
        if active_ticker_last_run:
            last_runs.append(('scrape-active-tickers', active_ticker_last_run))
        if daily_scraper_last_run:
            last_runs.append(('daily-scraper', daily_scraper_last_run))
        
        if last_runs:
            # Sort by timestamp and get the most recent
            last_runs.sort(key=lambda x: x[1], reverse=True)
            most_recent = last_runs[0]
            service_name = most_recent[0]
            
            # Map service names to user-friendly names
            service_display_names = {
                'run-sequential-scraping': 'Sequential Scraping',
                'scrape-active-tickers': 'Active Tickers',
                'daily-scraper': 'Daily Scraper'
            }
            
            display_name = service_display_names.get(service_name, service_name)
            last_run = f"{most_recent[1]} ({display_name})"
        else:
            last_run = 'Never'
        
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
            'current_script': config.get('script', 'run_sequential_scraping'),
            'service_last_runs': {
                'run_sequential_scraping': sequential_last_run or 'Never',
                'scrape_active_tickers': active_ticker_last_run or 'Never',
                'daily_scraper': daily_scraper_last_run or 'Never'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

@app.route('/start-active-scraper', methods=['POST'])
def start_active_scraper():
    """Start the active ticker scraper service"""
    try:
        subprocess.Popen(['systemctl', 'start', 'scrape-active-tickers.service'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({
            'success': True, 
            'message': 'Active ticker scraper service start command sent'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start active scraper service: {str(e)}'}), 500

@app.route('/start-hourly-service', methods=['POST'])
def start_hourly_service():
    """Start the hourly scraper service"""
    try:
        subprocess.Popen(['systemctl', 'start', 'hourly-scraper.service'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({
            'success': True, 
            'message': 'Hourly scraper service start command sent'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start hourly service: {str(e)}'}), 500

@app.route('/stop-hourly-service', methods=['POST'])
def stop_hourly_service():
    """Stop the hourly scraper service"""
    try:
        subprocess.Popen(['systemctl', 'stop', 'hourly-scraper.service'], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return jsonify({
            'success': True, 
            'message': 'Hourly scraper service stop command sent'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to stop hourly service: {str(e)}'}), 500

@app.route('/hourly-config', methods=['POST'])
def update_hourly_config():
    """Update which hourly script should run"""
    data = request.get_json()
    script = data.get('script')
    
    if script not in ['hourly_scraping', 'scrape_all_active_ticker_hourly']:
        return jsonify({'error': 'Invalid script. Must be hourly_scraping or scrape_all_active_ticker_hourly'}), 400
    
    try:
        import json
        config = {'script': script}
        with open('/root/dan_scraper/pro-api/hourly_scraper_config.json', 'w') as f:
            json.dump(config, f)
        
        return jsonify({
            'success': True,
            'message': f'Hourly configuration updated to run {script}'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to update hourly config: {str(e)}'}), 500

@app.route('/update-hourly-timer', methods=['POST'])
def update_hourly_timer():
    """Update hourly scraper timer schedule"""
    data = request.get_json()
    schedule = data.get('schedule')
    
    if not schedule:
        return jsonify({'error': 'Schedule is required'}), 400
    
    timer_content = f"""[Unit]
Description=Hourly Scraper Timer
Requires=hourly-scraper.service

[Timer]
OnCalendar={schedule}

[Install]
WantedBy=timers.target"""
    
    try:
        subprocess.run(['systemctl', 'stop', 'hourly-scraper.timer'], check=False)
        
        with open('/root/dan_scraper/pro-api/hourly-scraper.timer', 'w') as f:
            f.write(timer_content)
        
        subprocess.run(['cp', '/root/dan_scraper/pro-api/hourly-scraper.timer', '/etc/systemd/system/'], check=True)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'start', 'hourly-scraper.timer'], check=True)
        
        return jsonify({'success': True, 'message': f'Hourly timer updated to: {schedule}'})
    except Exception as e:
        return jsonify({'error': f'Failed to update hourly timer: {str(e)}'}), 500

@app.route('/hourly-status', methods=['GET'])
def get_hourly_status():
    """Get hourly scraper status"""
    try:
        # Check service status
        result = subprocess.run(['systemctl', 'is-active', 'hourly-scraper.service'], 
                              capture_output=True, text=True)
        service_status = result.stdout.strip()
        
        # Check timer status
        result = subprocess.run(['systemctl', 'is-active', 'hourly-scraper.timer'], 
                              capture_output=True, text=True)
        timer_status = result.stdout.strip()
        
        # Get last run time from hourly services
        def get_last_run_time(service_name):
            try:
                result = subprocess.run(['systemctl', 'show', service_name, '--property=ExecMainStartTimestamp'], 
                                      capture_output=True, text=True)
                timestamp = result.stdout.strip().replace('ExecMainStartTimestamp=', '')
                return timestamp if timestamp and timestamp != '' and timestamp != 'n/a' else None
            except:
                return None
        
        # Check hourly services for last run
        hourly_scraping_last_run = get_last_run_time('hourly-scraping.service')
        active_ticker_hourly_last_run = get_last_run_time('scrape-active-tickers-hourly.service')
        hourly_scraper_last_run = get_last_run_time('hourly-scraper.service')
        
        # Find the most recent run
        last_runs = []
        if hourly_scraping_last_run:
            last_runs.append(('hourly-scraping', hourly_scraping_last_run))
        if active_ticker_hourly_last_run:
            last_runs.append(('scrape-active-tickers-hourly', active_ticker_hourly_last_run))
        if hourly_scraper_last_run:
            last_runs.append(('hourly-scraper', hourly_scraper_last_run))
        
        if last_runs:
            # Sort by timestamp and get the most recent
            last_runs.sort(key=lambda x: x[1], reverse=True)
            most_recent = last_runs[0]
            service_name = most_recent[0]
            
            # Map service names to user-friendly names
            service_display_names = {
                'hourly-scraping': 'Hourly Scraping',
                'scrape-active-tickers-hourly': 'Active Tickers Hourly',
                'hourly-scraper': 'Hourly Scraper'
            }
            
            display_name = service_display_names.get(service_name, service_name)
            last_run = f"{most_recent[1]} ({display_name})"
        else:
            last_run = 'Never'
        
        # Get current config
        import json
        try:
            with open('/root/dan_scraper/pro-api/hourly_scraper_config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {'script': 'hourly_scraping'}
        
        return jsonify({
            'service_status': service_status,
            'timer_status': timer_status,
            'last_run': last_run,
            'current_script': config.get('script', 'hourly_scraping'),
            'service_last_runs': {
                'hourly_scraping': hourly_scraping_last_run or 'Never',
                'scrape_active_tickers_hourly': active_ticker_hourly_last_run or 'Never',
                'hourly_scraper': hourly_scraper_last_run or 'Never'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get hourly status: {str(e)}'}), 500

@app.route('/run-manual-scraper', methods=['POST'])
def run_manual_scraper():
    """Run manual scraper for target tickers"""
    data = request.get_json()
    script = data.get('script')
    
    if script not in ['run_sequential_scraping', 'scrape_all_active_ticker']:
        return jsonify({'error': 'Invalid script. Must be run_sequential_scraping or scrape_all_active_ticker'}), 400
    
    try:
        # Send Firebase notification
        from firebase_notifier import FirebaseNotifier
        from datetime import datetime
        FirebaseNotifier.send_notification(
            title="Scraper Started",
            body=f"{script} started from mobile app",
            data={"script": script, "status": "started", "timestamp": str(datetime.now())}
        )
        
        if script == 'run_sequential_scraping':
            service_name = 'run-sequential-scraping-manually.service'
        else:
            service_name = 'scrape-active-tickers-manually.service'
        
        subprocess.Popen(['systemctl', 'start', service_name], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return jsonify({
            'success': True, 
            'message': f'Manual scraper started: {script}'
        })
    except Exception as e:
        return jsonify({'error': f'Failed to start manual scraper: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)