import psycopg2
import os

# Database connection
conn = psycopg2.connect(
    host='162.248.101.75',
    port='5432',
    dbname='stocklist',
    user='haystockuser',
    password='zro=+)1*-D9X'
)
cursor = conn.cursor()

try:
    # Count tickers with stock_ticker (not null and not empty)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM scrap_task 
        WHERE stock_ticker IS NOT NULL 
        AND stock_ticker != ''
    """)
    
    count = cursor.fetchone()[0]
    print(f"Number of tickers with stock_ticker: {count}")
    
    # Also show some examples
    cursor.execute("""
        SELECT symbol, stock_ticker 
        FROM scrap_task 
        WHERE stock_ticker IS NOT NULL 
        AND stock_ticker != ''
        LIMIT 10
    """)
    
    examples = cursor.fetchall()
    if examples:
        print("\nExamples:")
        for symbol, stock_ticker in examples:
            print(f"  {symbol} -> {stock_ticker}")

finally:
    cursor.close()
    conn.close()