import psycopg2
from config.settings import DB_CONFIG

def add_guru_fields():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            ALTER TABLE scraper_tasks 
            ADD COLUMN last_action TEXT,
            ADD COLUMN per_portfolio TEXT
        """)
        conn.commit()
        print("✅ Added 'last_action' and 'per_portfolio' fields to scraper_tasks table")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_guru_fields()