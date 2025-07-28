import psycopg2
from config.settings import DB_CONFIG

def add_active_field():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE scraper_tasks 
            ADD COLUMN active BOOLEAN DEFAULT FALSE
        """)
        conn.commit()
        print("✅ Added 'active' field to scraper_tasks table")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_active_field()