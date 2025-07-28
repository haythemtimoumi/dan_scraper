#!/usr/bin/env python
"""
FastAPI application for controlling the monthly ticker task scheduler
"""

import os
import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from .scheduler_service import scheduler_service

app = FastAPI(
    title="Monthly Ticker Task Scheduler API",
    description="API to control the monthly ticker task scheduler service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    schedule_type: Optional[str] = None  # monthly, weekly, daily, custom
    day_of_month: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    script_path: Optional[str] = None
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Monthly Ticker Task Scheduler API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/status",
            "start": "/start",
            "stop": "/stop",
            "run_now": "/run-now",
            "config": "/config",
            "dashboard": "/dashboard"
        }
    }

@app.get("/status")
async def get_status():
    """Get current scheduler status"""
    return scheduler_service.get_status()

@app.post("/start")
async def start_scheduler():
    """Start the scheduler service"""
    success = scheduler_service.start()
    if success:
        return {"message": "Scheduler started successfully", "status": "started"}
    else:
        raise HTTPException(status_code=400, detail="Scheduler is already running")

@app.post("/stop")
async def stop_scheduler():
    """Stop the scheduler service"""
    success = scheduler_service.stop()
    if success:
        return {"message": "Scheduler stopped successfully", "status": "stopped"}
    else:
        raise HTTPException(status_code=400, detail="Scheduler is not running")

@app.post("/run-now")
async def run_now():
    """Run the task immediately"""
    success, message = scheduler_service.run_now()
    if success:
        return {"message": message, "status": "task_started"}
    else:
        raise HTTPException(status_code=400, detail=message)

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return scheduler_service.config

@app.put("/config")
async def update_config(config_update: ConfigUpdate):
    """Update scheduler configuration"""
    # Convert to dict and remove None values
    update_dict = {k: v for k, v in config_update.dict().items() if v is not None}
    
    # Validate values
    if "schedule_type" in update_dict:
        if update_dict["schedule_type"] not in ["monthly", "weekly", "daily", "custom"]:
            raise HTTPException(status_code=400, detail="Invalid schedule_type")
    
    if "day_of_month" in update_dict:
        if not 1 <= update_dict["day_of_month"] <= 31:
            raise HTTPException(status_code=400, detail="day_of_month must be between 1 and 31")
    
    if "hour" in update_dict:
        if not 0 <= update_dict["hour"] <= 23:
            raise HTTPException(status_code=400, detail="hour must be between 0 and 23")
    
    if "minute" in update_dict:
        if not 0 <= update_dict["minute"] <= 59:
            raise HTTPException(status_code=400, detail="minute must be between 0 and 59")
    
    success, message = scheduler_service.update_config(update_dict)
    if success:
        return {"message": message, "config": scheduler_service.config}
    else:
        raise HTTPException(status_code=500, detail=message)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple HTML dashboard for controlling the scheduler"""
    status = scheduler_service.get_status()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monthly Ticker Task Scheduler</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; }}
            .status {{ padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .status.running {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
            .status.stopped {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
            .status.waiting {{ background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }}
            .controls {{ margin: 20px 0; }}
            button {{ padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }}
            .btn-primary {{ background-color: #007bff; color: white; }}
            .btn-success {{ background-color: #28a745; color: white; }}
            .btn-danger {{ background-color: #dc3545; color: white; }}
            .btn-warning {{ background-color: #ffc107; color: black; }}
            .config {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .config-item {{ margin: 10px 0; }}
            input, select {{ padding: 5px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; }}
            .form-group {{ margin: 15px 0; }}
            label {{ display: inline-block; width: 150px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Monthly Ticker Task Scheduler</h1>
            
            <div class="status {status['status']}">
                <strong>Status:</strong> {status['status'].upper()}<br>
                <strong>Service Running:</strong> {'Yes' if status['running'] else 'No'}<br>
                <strong>Next Run:</strong> {status['next_run'] or 'Not scheduled'}<br>
                <strong>Last Run:</strong> {status['last_run'] or 'Never'}
            </div>
            
            <div class="controls">
                <button class="btn-success" onclick="startScheduler()">Start Scheduler</button>
                <button class="btn-danger" onclick="stopScheduler()">Stop Scheduler</button>
                <button class="btn-warning" onclick="runNow()">Run Now</button>
                <button class="btn-primary" onclick="refreshStatus()">Refresh Status</button>
            </div>
            
            <div class="config">
                <h3>Configuration</h3>
                <form id="configForm">
                    <div class="form-group">
                        <label>Enabled:</label>
                        <select id="enabled">
                            <option value="true" {'selected' if status['config']['enabled'] else ''}>Yes</option>
                            <option value="false" {'selected' if not status['config']['enabled'] else ''}>No</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Schedule Type:</label>
                        <select id="schedule_type">
                            <option value="monthly" {'selected' if status['config']['schedule_type'] == 'monthly' else ''}>Monthly</option>
                            <option value="weekly" {'selected' if status['config']['schedule_type'] == 'weekly' else ''}>Weekly</option>
                            <option value="daily" {'selected' if status['config']['schedule_type'] == 'daily' else ''}>Daily</option>
                            <option value="custom" {'selected' if status['config']['schedule_type'] == 'custom' else ''}>Custom</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Day of Month:</label>
                        <input type="number" id="day_of_month" min="1" max="31" value="{status['config']['day_of_month']}">
                    </div>
                    
                    <div class="form-group">
                        <label>Hour (0-23):</label>
                        <input type="number" id="hour" min="0" max="23" value="{status['config']['hour']}">
                    </div>
                    
                    <div class="form-group">
                        <label>Minute (0-59):</label>
                        <input type="number" id="minute" min="0" max="59" value="{status['config']['minute']}">
                    </div>
                    
                    <div class="form-group">
                        <label>Max Retries:</label>
                        <input type="number" id="max_retries" min="1" max="10" value="{status['config']['max_retries']}">
                    </div>
                    
                    <button type="button" class="btn-primary" onclick="updateConfig()">Update Configuration</button>
                </form>
            </div>
        </div>
        
        <script>
            async function apiCall(endpoint, method = 'GET', data = null) {{
                const options = {{
                    method: method,
                    headers: {{ 'Content-Type': 'application/json' }}
                }};
                
                if (data) {{
                    options.body = JSON.stringify(data);
                }}
                
                try {{
                    const response = await fetch(endpoint, options);
                    const result = await response.json();
                    
                    if (!response.ok) {{
                        alert('Error: ' + (result.detail || 'Unknown error'));
                        return null;
                    }}
                    
                    return result;
                }} catch (error) {{
                    alert('Network error: ' + error.message);
                    return null;
                }}
            }}
            
            async function startScheduler() {{
                const result = await apiCall('/start', 'POST');
                if (result) {{
                    alert(result.message);
                    location.reload();
                }}
            }}
            
            async function stopScheduler() {{
                const result = await apiCall('/stop', 'POST');
                if (result) {{
                    alert(result.message);
                    location.reload();
                }}
            }}
            
            async function runNow() {{
                const result = await apiCall('/run-now', 'POST');
                if (result) {{
                    alert(result.message);
                    location.reload();
                }}
            }}
            
            async function refreshStatus() {{
                location.reload();
            }}
            
            async function updateConfig() {{
                const config = {{
                    enabled: document.getElementById('enabled').value === 'true',
                    schedule_type: document.getElementById('schedule_type').value,
                    day_of_month: parseInt(document.getElementById('day_of_month').value),
                    hour: parseInt(document.getElementById('hour').value),
                    minute: parseInt(document.getElementById('minute').value),
                    max_retries: parseInt(document.getElementById('max_retries').value)
                }};
                
                const result = await apiCall('/config', 'PUT', config);
                if (result) {{
                    alert(result.message);
                    location.reload();
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)