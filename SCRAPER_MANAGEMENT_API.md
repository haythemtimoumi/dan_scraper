# Scraper Management API Documentation

Base URL: `https://stock-ticker.dev`

## Service Control Endpoints

### Get Available Services
```http
GET /services
```

**Response:**
```json
{
  "services": [
    "month-rule.service",
    "stockscores-to-db.service", 
    "rule1-guru-to-db.service",
    "dan-watchlist-to-db.service",
    "rule1-list-to-db.service",
    "run-sequential-scraping.service",
    "main-scraper.service"
  ]
}
```

### Run Individual Service
```http
POST /run-service
Content-Type: application/json

{
  "service": "service-name.service"
}
```

**Examples:**
```bash
# Run all scrapers together
curl -X POST -H "Content-Type: application/json" \
  -d '{"service":"main-scraper.service"}' \
  https://stock-ticker.dev/run-service

# Run StockScores scraper only
curl -X POST -H "Content-Type: application/json" \
  -d '{"service":"stockscores-to-db.service"}' \
  https://stock-ticker.dev/run-service

# Run Rule1 + GuruFocus scraper
curl -X POST -H "Content-Type: application/json" \
  -d '{"service":"rule1-guru-to-db.service"}' \
  https://stock-ticker.dev/run-service
```

### Update Timer Schedule
```http
POST /update-timer
Content-Type: application/json

{
  "schedule": "daily"
}
```

**Schedule Options:**
- `"daily"` - Run daily at midnight
- `"weekly"` - Run weekly on Sunday
- `"monthly"` - Run monthly on 1st
- `"*-*-* 09:00:00"` - Custom time format

## Service Descriptions

| Service | Description | Use Case |
|---------|-------------|----------|
| `main-scraper.service` | **Runs all scrapers** | Complete data collection |
| `stockscores-to-db.service` | StockScores scraper | Technical analysis data |
| `rule1-guru-to-db.service` | Rule1 + GuruFocus | Fundamental analysis |
| `dan-watchlist-to-db.service` | Personal watchlist | Your tracked stocks |
| `rule1-list-to-db.service` | Rule1 ticker discovery | Find new stocks |
| `run-sequential-scraping.service` | Sequential processing | Ordered execution |
| `month-rule.service` | Monthly processing | Monthly tasks |

## Response Formats

**Success Response:**
```json
{
  "success": true,
  "message": "service-name.service started"
}
```

**Error Response:**
```json
{
  "error": "Failed to start service-name.service: error details"
}
```

## Integration Examples

### JavaScript/React
```javascript
const runScraper = async (serviceName) => {
  const response = await fetch('https://stock-ticker.dev/run-service', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ service: serviceName })
  });
  return response.json();
};

// Run all scrapers
await runScraper('main-scraper.service');
```

### Python
```python
import requests

def run_service(service_name):
    response = requests.post(
        'https://stock-ticker.dev/run-service',
        json={'service': service_name}
    )
    return response.json()

# Run all scrapers
result = run_service('main-scraper.service')
```

## Recommended Usage

1. **Full Data Collection**: Use `main-scraper.service`
2. **Individual Sources**: Use specific service endpoints
3. **Scheduling**: Use `/update-timer` for automation
4. **Monitoring**: Check service status via systemctl on server

## Notes

- Services may take 30+ minutes to complete
- Use `main-scraper.service` for complete pipeline
- Individual services can be run for targeted data collection
- All services save data to database with S3 backup