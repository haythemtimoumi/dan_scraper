import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from datetime import datetime
from config.settings import DB_CONFIG

def get_db_connection():
    """
    Create a connection to the PostgreSQL database
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def clean_price_value(value):
    """Clean price values by removing $ and commas"""
    if isinstance(value, str):
        return value.replace('$', '').replace(',', '')
    return value

def clean_percentage(value):
    """Clean percentage values by removing %"""
    if isinstance(value, str):
        return value.replace('%', '')
    return value

def safe_convert_to_int(value):
    """Safely convert a value to integer, or return None if not possible"""
    if value is None:
        return None
    try:
        # First try direct conversion
        return int(value)
    except (ValueError, TypeError):
        try:
            # Try converting to float first (for values like '98.0')
            return int(float(value))
        except (ValueError, TypeError):
            return None

def save_stock_data_to_db(data, source='rule1'):
    """
    Save stock data to the PostgreSQL database
    
    Args:
        data: DataFrame or list of dictionaries containing stock data
        source: Source of the data ('rule1' or 'manual')
    
    Returns:
        bool: True if successful, False otherwise
    """
    if isinstance(data, pd.DataFrame):
        records = data.to_dict('records')
    else:
        records = data
    
    if not records:
        print("⚠️ No data to save to database")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        # Prepare data for batch insert
        batch_data = []
        for record in records:
            # Clean price values before inserting
            last_price = clean_price_value(record.get('last_price'))
            buy_price = clean_price_value(record.get('buy_price'))
            percentage_upside = clean_percentage(record.get('percentage_upside'))
            
            # Map CSV columns to database columns
            db_record = (
                record.get('Date', current_timestamp),          # timestamp
                record.get('ticker', ''),                       # ticker
                source,                                         # source
                percentage_upside,                              # pe (now percentage_upside)
                None,                                           # dividend
                None,                                           # cash_per_share
                last_price,                                     # current_ratio (now last_price)
                safe_convert_to_int(record.get('signal_score', record.get('Signal Score'))),  # signal_score
                safe_convert_to_int(record.get('sentiment_score', record.get('Sentiment Score'))),  # sentiment_score
                record.get('screenshot', record.get('Screenshot', '')),  # screenshot
                None,                                           # guru
                record.get('rule1_score'),                      # rule1_score
                record.get('moat_score'),                       # moat_score
                record.get('management_score'),                 # management_score
                buy_price                                       # buy_price
            )
            batch_data.append(db_record)
        
        # Simple INSERT without ON CONFLICT since we don't have a unique constraint
        query = """
        INSERT INTO stock_analysis (
            date, ticker, source, pe, dividend, cash_per_share, current_ratio,
            signal_score, sentiment_score, screenshot, guru, rule1_score,
            moat_score, management_score, buy_price
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Execute batch insert
        execute_batch(cursor, query, batch_data)
        conn.commit()
        
        print(f"✅ Successfully saved {len(batch_data)} records to database with source '{source}'")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving to database: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()