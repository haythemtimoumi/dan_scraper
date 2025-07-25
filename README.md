# Stock Data Scraper

A comprehensive Python-based web scraper that automatically collects financial data from multiple sources for stock analysis and investment decisions.

## What This Project Does

This tool scrapes financial metrics from multiple sources and combines them into a unified dataset:

**Data Sources:**
- **Rule1Toolbox** - Investment scoring, valuation metrics, and ticker discovery
- **StockScores** - Technical analysis, sentiment data, and chart screenshots
- **GuruFocus** - Portfolio tracking and additional metrics
- **Yahoo Finance** - Real-time stock prices

**Collected Metrics:**
- Rule1 Score, Management Score, Moat Score
- Sticker Price (calculated fair value) vs Last Price
- Percentage Upside potential
- Dividend yield and Cash Per Share
- Signal Score and Sentiment Score
- Chart screenshots for technical analysis

## Key Features

- **Complete Pipeline** - One command runs entire data collection process
- **Smart Resume** - Automatically continues from where scraping stopped
- **Multi-Source Integration** - Combines data from 4+ financial platforms
- **Database Storage** - Saves data to database with S3 backup
- **Retry Logic** - Handles failures with automatic retries
- **Email Verification** - Auto-handles 2FA email codes
- **Source Tracking** - Tracks which source provided each ticker

## Quick Start

```bash
# Run complete pipeline (recommended)
python run_all_in_one.py

# Manual email verification
python run_all_in_one.py --manual-verify

# Resume interrupted scraping
python smart_resume_scraper.py

# Resume with visible browser
python smart_resume_scraper.py --visible
```

## Output Files

- `ticker_data_fixed.csv` - Main output with all financial metrics
- `stockscores_data.csv` - Technical analysis data
- `guru_data.csv` - Portfolio tracking data
- `data/ticker_sources.csv` - Source tracking for each ticker

## Requirements

- Python 3.6+
- Chrome browser
- `.env` file with credentials for all platforms
- AWS credentials for S3 upload (optional)