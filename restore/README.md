# Database Restore Tool

Restores database from S3 backup files to your local PostgreSQL database.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS credentials:**
   ```bash
   aws configure
   # OR set environment variables:
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

3. **Update database config in `config.py`:**
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'port': '5432',
       'database': 'your_db_name',
       'user': 'your_username',
       'password': 'your_password'
   }
   ```

## Usage

```bash
python restore_database.py
```

## Restore Options

1. **Complete Restore (JSON)** - Restores all tables with complete data
2. **Main Table Only (CSV)** - Restores only stock_analysis table

## Files Downloaded

- `database_backup_DD_MM_YYYY.json` - Complete database backup
- `database_backup_DD_MM_YYYY.csv` - Main table backup

## Database Tables

- comment
- guru  
- guru_ticker_map
- old_stock_analysis
- scraper_tasks
- stock_analysis (main table)
- users