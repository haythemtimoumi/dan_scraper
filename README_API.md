# Monthly Ticker Task Scheduler API

A service and API to automatically run the monthly ticker task on a configurable schedule.

## Features

- **Configurable Schedule**: Monthly, weekly, daily, or custom scheduling
- **Web Dashboard**: Easy-to-use web interface for control
- **REST API**: Full API for programmatic control
- **Automatic Retries**: Configurable retry logic for failed tasks
- **Status Monitoring**: Real-time status and next run information

## Quick Start

### 1. Install Dependencies

```bash
pip install -r api/requirements.txt
```

### 2. Run the API Server

```bash
python run_api.py
```

The API will be available at:
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000

### 3. Run as Standalone Service

```bash
python service_runner.py
```

## API Endpoints

### GET /status
Get current scheduler status
```json
{
  "running": true,
  "status": "waiting",
  "next_run": "2024-02-01T09:00:00",
  "last_run": "2024-01-01T09:00:00",
  "config": {...}
}
```

### POST /start
Start the scheduler service

### POST /stop
Stop the scheduler service

### POST /run-now
Run the task immediately

### GET /config
Get current configuration

### PUT /config
Update configuration
```json
{
  "enabled": true,
  "schedule_type": "monthly",
  "day_of_month": 1,
  "hour": 9,
  "minute": 0,
  "max_retries": 3,
  "retry_delay": 300
}
```

## Configuration Options

- **enabled**: Enable/disable the scheduler
- **schedule_type**: "monthly", "weekly", "daily", or "custom"
- **day_of_month**: Day of month to run (1-31, for monthly schedule)
- **hour**: Hour to run (0-23)
- **minute**: Minute to run (0-59)
- **script_path**: Path to the script to run
- **max_retries**: Maximum retry attempts
- **retry_delay**: Delay between retries (seconds)

## Web Dashboard

Access the web dashboard at http://localhost:8000/dashboard to:
- View current status
- Start/stop the scheduler
- Run tasks immediately
- Update configuration
- Monitor next run time

## Usage Examples

### Start the scheduler
```bash
curl -X POST http://localhost:8000/start
```

### Update schedule to run daily at 2:30 AM
```bash
curl -X PUT http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"schedule_type": "daily", "hour": 2, "minute": 30}'
```

### Run task immediately
```bash
curl -X POST http://localhost:8000/run-now
```

### Check status
```bash
curl http://localhost:8000/status
```

## Configuration File

The service saves configuration to `api/scheduler_config.json`. You can edit this file directly or use the API/dashboard.

## Running as Windows Service

To run as a Windows service, you can use tools like `nssm` or `sc` to register `service_runner.py` as a system service.

## Logs

The service outputs logs to stdout. For production, redirect to a log file:
```bash
python service_runner.py > scheduler.log 2>&1
```