#!/usr/bin/env python
import psycopg2

def create_schema():
    try:
        conn = psycopg2.connect(
            dbname='stocklist',
            user='haystockuser',
            password='zro=+)1*-D9X',
            host='localhost',
            port='5432'
        )
        cursor = conn.cursor()
        
        # Create scraper_task table
        cursor.execute("""
            CREATE TABLE public.scraper_task (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created scraper_task table")
        
        # Add id column to stock_analysis
        cursor.execute("ALTER TABLE public.stock_analysis ADD COLUMN id SERIAL PRIMARY KEY")
        print("Added id column to stock_analysis")
        
        # Add foreign key constraint
        cursor.execute("""
            ALTER TABLE public.stock_analysis 
            ADD CONSTRAINT fk_stock_analysis_ticker 
            FOREIGN KEY (ticker_id) REFERENCES public.scraper_task(id)
        """)
        print("Added foreign key constraint")
        
        conn.commit()
        print("Schema created successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_schema()