import psycopg2
from config.settings import DB_CONFIG

def create_scraper_tasks_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    create_table_sql = """
    CREATE TABLE scraper_tasks (
      id SERIAL PRIMARY KEY,
      symbol TEXT NOT NULL,
      guru_name TEXT,
      list_type TEXT,
      scrape_type TEXT NOT NULL,
      scrape_status TEXT DEFAULT 'pending',
      current_step TEXT DEFAULT 'rule1',
      retry_count INTEGER DEFAULT 0,
      last_updated_rule1_at TIMESTAMP,
      last_updated_stockscore_at TIMESTAMP,
      last_updated_lastprice_at TIMESTAMP,
      UNIQUE(symbol, guru_name, list_type)
    );
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("Table 'scraper_tasks' created successfully!")

if __name__ == "__main__":
    create_scraper_tasks_table()