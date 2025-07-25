DB_CONFIG = {
    'dbname': 'stocklist',      # Your database name (default is 'postgres')
    'user': 'haystockuser',        # Your PostgreSQL username (default is 'postgres')
    'password': 'zro=+)1*-D9X', # Your PostgreSQL password (change if needed)
    'host': '162.248.101.75',       # VPS server (currently unreachable)
    #'host': 'localhost',              # Use localhost for now
    'port': '5432'             # Default PostgreSQL port (5432)
}

# S3 Configuration
S3_CONFIG = {
    'bucket_name': 'dan-scraper-csv-files',  # Replace with your actual bucket name
    'region': 'ca-central-1'
}
