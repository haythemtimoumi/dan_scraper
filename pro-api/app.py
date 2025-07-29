#!/usr/bin/env python
"""API for managing scraper services at stock-ticker.dev"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os

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
    'main-scraper.service'
]

@app.route('/run-service', methods=['POST'])
def run_service():
    """Run a specific service"""
    data = request.get_json()
    service_name = data.get('service')
    
    if service_name not in SERVICES:
        return jsonify({'error': 'Invalid service name'}), 400
    
    try:
        result = subprocess.run(['systemctl', 'start', service_name], 
                              capture_output=True, text=True, check=True)
        return jsonify({'success': True, 'message': f'{service_name} started'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Failed to start {service_name}: {e.stderr}'}), 500

@app.route('/update-timer', methods=['POST'])
def update_timer():
    """Update main-scraper timer schedule"""
    data = request.get_json()
    schedule = data.get('schedule')
    
    if not schedule:
        return jsonify({'error': 'Schedule is required'}), 400
    
    timer_content = f"""[Unit]
Description=Run Main Scraper on schedule

[Timer]
OnCalendar={schedule}

[Install]
WantedBy=timers.target"""
    
    try:
        # Stop timer first to prevent automatic execution
        subprocess.run(['systemctl', 'stop', 'main-scraper.timer'], check=True)
        
        # Write new timer file
        with open('/etc/systemd/system/main-scraper.timer', 'w') as f:
            f.write(timer_content)
        
        # Reload systemd and start timer (not restart)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'start', 'main-scraper.timer'], check=True)
        
        return jsonify({'success': True, 'message': f'Timer updated to: {schedule}'})
    except Exception as e:
        return jsonify({'error': f'Failed to update timer: {str(e)}'}), 500

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
            'update_timer': '/update-timer'
        }
    })

@app.route('/services', methods=['GET'])
def list_services():
    """List available services"""
    return jsonify({'services': SERVICES})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)