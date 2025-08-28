# Database Restore Configuration
# Update these settings for your local PC

# S3 Configuration (keep as is)
S3_CONFIG = {
    'bucket_name': 'dan-scraper-csv-files',
    'region': 'ca-central-1'
}

# Database Configuration (UPDATE FOR YOUR LOCAL PC)
DB_CONFIG = {
    'host': 'localhost',          # Your local database host
    'port': '5432',               # Your local database port
    'dbname': 'stocklist',        # Your local database name
    'user': 'haystockuser',       # Your local database user
    'password': 'zro=+)1*-D9X'    # Your local database password
}

# Production Database (for reference)
PROD_DB_CONFIG = {
    'host': '162.248.101.75',
    'port': '5432',
    'database': 'stocklist',
    'user': 'haystockuser',
    'password': 'zro=+)1*-D9X'
}