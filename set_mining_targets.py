#!/usr/bin/env python
"""Set mining/gold tickers as targets for scraping"""

import psycopg2
from config.settings import DB_CONFIG

def set_mining_targets():
    """Set mining/gold tickers as targets with Dan as guru"""
    
    # Mining/gold tickers to target
    mining_tickers = [
        'UUUU', 'AUMB', 'AAUC', 'USA', 'APM', 'ARIS', 'ARTG', 'ASM', 'AYA', 
        'BTO', 'CBR', 'CDE', 'DSV', 'DPM', 'ELD', 'EDV', 'EDR', 'EQX', 'AG', 
        'FVI', 'FVL', 'GGD', 'GSVR', 'HL', 'HSTR', 'JAG', 'LG', 'MSA', 'NEXG', 
        'PAAS', 'PRU', 'RVG', 'RIO', 'SSRM', 'SLVR', 'SVM', 'SKE', 'STGO', 
        'TSK', 'VZLA', 'WRLG', 'WVM', 'WGX', 'AEM', 'AGI', 'AU', 'B', 'GFI', 
        'KGC', 'NEM'
    ]
    
    DAN_GURU_ID = 1231  # Dan's guru_id from guru table
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # First, clear existing targets
        cursor.execute("UPDATE scraper_tasks SET target = false")
        print("Cleared existing targets")
        
        # Set new targets with Dan as guru and ensure they're pending
        placeholders = ','.join(['%s'] * len(mining_tickers))
        cursor.execute(f"""
            UPDATE scraper_tasks 
            SET target = true, scrape_status = 'pending', guru_id = {DAN_GURU_ID}
            WHERE UPPER(symbol) IN ({placeholders})
        """, [ticker.upper() for ticker in mining_tickers])
        
        updated_count = cursor.rowcount
        
        # Ensure guru_ticker_map entries exist for Dan
        cursor.execute(f"""
            INSERT INTO guru_ticker_map (guru_id, scraper_task_id, per_port, last_act)
            SELECT %s, st.id, '0%', 'hold'
            FROM scraper_tasks st 
            WHERE st.target = true AND st.guru_id = %s
            ON CONFLICT (guru_id, scraper_task_id) DO NOTHING
        """, (DAN_GURU_ID, DAN_GURU_ID))
        
        # Check which tickers were found
        cursor.execute("""
            SELECT symbol FROM scraper_tasks 
            WHERE target = true
            ORDER BY symbol
        """)
        results = cursor.fetchall()
        found_tickers = [row[0] for row in results] if results else []
        
        # Find missing tickers
        found_upper = [t.upper() for t in found_tickers]
        missing = [t for t in mining_tickers if t.upper() not in found_upper]
        
        conn.commit()
        
        print(f"\n✅ Set {updated_count} tickers as targets with Dan (guru_id: {DAN_GURU_ID})")
        print(f"Found tickers: {', '.join(found_tickers)}")
        if missing:
            print(f"Missing tickers: {', '.join(missing)}")
        
        return updated_count
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    set_mining_targets()