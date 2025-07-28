#!/usr/bin/env python
"""
Simple HTTP server for scheduler control without FastAPI dependency
"""

import os
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from api.scheduler_service import scheduler_service

class SchedulerHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            response = {
                "message": "Monthly Ticker Task Scheduler API",
                "endpoints": {
                    "status": "/status",
                    "start": "/start",
                    "stop": "/stop",
                    "run_now": "/run-now",
                    "config": "/config"
                }
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            status = scheduler_service.get_status()
            self.wfile.write(json.dumps(status, default=str).encode())
            
        elif path == '/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(scheduler_service.config).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/start':
            success = scheduler_service.start()
            if success:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"message": "Scheduler started successfully", "status": "started"}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"error": "Scheduler is already running"}
                self.wfile.write(json.dumps(response).encode())
                
        elif path == '/stop':
            success = scheduler_service.stop()
            if success:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"message": "Scheduler stopped successfully", "status": "stopped"}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"error": "Scheduler is not running"}
                self.wfile.write(json.dumps(response).encode())
                
        elif path == '/run-now':
            success, message = scheduler_service.run_now()
            if success:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"message": message, "status": "task_started"}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"error": message}
                self.wfile.write(json.dumps(response).encode())
                
        elif path == '/config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                config_update = json.loads(post_data.decode('utf-8'))
                success, message = scheduler_service.update_config(config_update)
                if success:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    response = {"message": message, "config": scheduler_service.config}
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self._set_cors_headers()
                    self.end_headers()
                    response = {"error": message}
                    self.wfile.write(json.dumps(response).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                response = {"error": "Invalid JSON"}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

def run_server():
    server = HTTPServer(('localhost', 8000), SchedulerHandler)
    print("Starting Monthly Ticker Task Scheduler API...")
    print("API available at: http://localhost:8000")
    print("Status: http://localhost:8000/status")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_server()