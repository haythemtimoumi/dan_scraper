#!/usr/bin/env python
import psycopg2
import os

# Database connection
os.environ['PGPASSWORD'] = 'zro=+)1*-D9X'

try:
    conn = psycopg2.connect(
        host='162.248.101.75',
        port=5432,
        database='stocklist',
        user='haystockuser'
    )
    cursor = conn.cursor()
    
    print("=== COMPANY TABLE DATA ===")
    cursor.execute("SELECT COUNT(*) FROM company WHERE DATE(created_at) = '2024-09-19'")
    count = cursor.fetchone()[0]
    print(f"Records on 2024-09-19: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, ticker, full_name, created_at FROM company WHERE DATE(created_at) = '2024-09-19' LIMIT 5")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Ticker: {row[1]}, Name: {row[2]}, Created: {row[3]}")
    
    print("\n=== STOCK_ANALYSIS TABLE DATA ===")
    cursor.execute("SELECT COUNT(*) FROM stock_analysis WHERE DATE(date) = '2024-09-19'")
    count = cursor.fetchone()[0]
    print(f"Records on 2024-09-19: {count}")
    
    if count > 0:
        cursor.execute("SELECT ticker, rule1_score, buy_price, last_price, date FROM stock_analysis WHERE DATE(date) = '2024-09-19' LIMIT 5")
        for row in cursor.fetchall():
            print(f"Ticker: {row[0]}, Rule1: {row[1]}, Buy: {row[2]}, Last: {row[3]}, Date: {row[4]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")