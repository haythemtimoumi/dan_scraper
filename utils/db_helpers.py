#!/usr/bin/env python
"""
Database helper functions for handling guru_ticker_map table
"""

import psycopg2
from config.settings import DB_CONFIG

def insert_ticker_with_guru_map(symbol, guru_name, list_type, scrape_type='monthly', active=True, scrape_status='pending', **kwargs):
    """
    Insert ticker into scraper_tasks and create guru_ticker_map entry if not exists
    Returns: (ticker_id, created) where created is True if new record was created
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get or create guru
        cursor.execute("""
            INSERT INTO guru (guru_name, description) 
            VALUES (%s, %s) 
            ON CONFLICT (guru_name) DO NOTHING 
            RETURNING id
        """, (guru_name, f"Portfolio for {guru_name}"))
        
        guru_result = cursor.fetchone()
        if guru_result:
            guru_id = guru_result[0]
        else:
            cursor.execute("SELECT id FROM guru WHERE guru_name = %s", (guru_name,))
            guru_id = cursor.fetchone()[0]
        
        # Check if ticker already exists for this guru and list_type
        cursor.execute("""
            SELECT id FROM scraper_tasks 
            WHERE symbol = %s AND guru_id = %s AND list_type = %s
        """, (symbol, guru_id, list_type))
        
        existing_ticker = cursor.fetchone()
        
        if existing_ticker:
            ticker_id = existing_ticker[0]
            # Update existing ticker
            cursor.execute("""
                UPDATE scraper_tasks 
                SET active = %s, scrape_status = %s, last_action = %s, per_portfolio = %s
                WHERE id = %s
            """, (active, scrape_status, kwargs.get('last_action'), kwargs.get('per_portfolio'), ticker_id))
            
            # Ensure guru_ticker_map entry exists
            cursor.execute("""
                INSERT INTO guru_ticker_map (guru_id, scraper_task_id)
                VALUES (%s, %s)
                ON CONFLICT (guru_id, scraper_task_id) DO NOTHING
            """, (guru_id, ticker_id))
            
            conn.commit()
            return ticker_id, False
        else:
            # Insert new ticker
            cursor.execute("""
                INSERT INTO scraper_tasks (symbol, guru_id, list_type, scrape_type, active, scrape_status, last_action, per_portfolio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (symbol, guru_id, list_type, scrape_type, active, scrape_status, kwargs.get('last_action'), kwargs.get('per_portfolio')))
            
            ticker_id = cursor.fetchone()[0]
            
            # Insert into guru_ticker_map
            cursor.execute("""
                INSERT INTO guru_ticker_map (guru_id, scraper_task_id)
                VALUES (%s, %s)
            """, (guru_id, ticker_id))
            
            conn.commit()
            return ticker_id, True
            
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def bulk_insert_tickers_with_guru_map(tickers_data):
    """
    Bulk insert tickers with guru mapping
    tickers_data: list of dicts with keys: symbol, guru_name, list_type, etc.
    Returns: (total_processed, new_created, updated)
    """
    total_processed = 0
    new_created = 0
    updated = 0
    
    for ticker_data in tickers_data:
        try:
            ticker_id, created = insert_ticker_with_guru_map(**ticker_data)
            total_processed += 1
            if created:
                new_created += 1
            else:
                updated += 1
        except Exception as e:
            print(f"Error processing {ticker_data.get('symbol', 'unknown')}: {e}")
    
    return total_processed, new_created, updated