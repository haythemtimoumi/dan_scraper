#!/usr/bin/env python
import psycopg2
from config.settings import DB_CONFIG

def fix_database_schema():
    """Fix database schema by adding PK, FK, and id column to stock_analysis"""
    
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        cursor = conn.cursor()
        
        print("🔍 Checking current table structures...")
        
        # Check scraper_task table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'scraper_task' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        scraper_task_columns = cursor.fetchall()
        print(f"📊 scraper_task columns: {scraper_task_columns}")
        
        # Check stock_analysis table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'stock_analysis' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        stock_analysis_columns = cursor.fetchall()
        print(f"📊 stock_analysis columns: {stock_analysis_columns}")
        
        # Add id column to stock_analysis if it doesn't exist
        has_id = any(col[0] == 'id' for col in stock_analysis_columns)
        if not has_id:
            print("➕ Adding id column to stock_analysis...")
            cursor.execute("ALTER TABLE public.stock_analysis ADD COLUMN id SERIAL PRIMARY KEY")
        
        # Add primary key to scraper_task if it doesn't exist
        cursor.execute("""
            SELECT constraint_name FROM information_schema.table_constraints 
            WHERE table_name = 'scraper_task' AND constraint_type = 'PRIMARY KEY'
        """)
        scraper_task_pk = cursor.fetchone()
        
        if not scraper_task_pk:
            has_scraper_id = any(col[0] == 'id' for col in scraper_task_columns)
            if not has_scraper_id:
                print("➕ Adding id column to scraper_task...")
                cursor.execute("ALTER TABLE public.scraper_task ADD COLUMN id SERIAL PRIMARY KEY")
            else:
                print("➕ Adding primary key to scraper_task...")
                cursor.execute("ALTER TABLE public.scraper_task ADD PRIMARY KEY (id)")
        
        # Add foreign key relationship
        cursor.execute("""
            SELECT constraint_name FROM information_schema.table_constraints 
            WHERE table_name = 'stock_analysis' AND constraint_type = 'FOREIGN KEY'
        """)
        fk_exists = cursor.fetchone()
        
        if not fk_exists:
            print("➕ Adding foreign key relationship...")
            cursor.execute("""
                ALTER TABLE public.stock_analysis 
                ADD CONSTRAINT fk_stock_analysis_ticker 
                FOREIGN KEY (ticker_id) REFERENCES public.scraper_task(id)
            """)
        
        conn.commit()
        print("✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_database_schema()