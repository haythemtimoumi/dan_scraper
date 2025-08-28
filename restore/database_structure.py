#!/usr/bin/env python3
"""
Database Structure Setup
Creates all tables with exact structure from production database
"""

import psycopg2
from config import DB_CONFIG

def create_database_structure():
    """Create all database tables with exact production structure"""
    print("🏗️ Creating database structure...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Drop existing tables (optional - uncomment if needed)
    # drop_tables = """
    # DROP TABLE IF EXISTS comment CASCADE;
    # DROP TABLE IF EXISTS guru CASCADE;
    # DROP TABLE IF EXISTS guru_ticker_map CASCADE;
    # DROP TABLE IF EXISTS old_stock_analysis CASCADE;
    # DROP TABLE IF EXISTS scraper_tasks CASCADE;
    # DROP TABLE IF EXISTS stock_analysis CASCADE;
    # DROP TABLE IF EXISTS users CASCADE;
    # """
    # cursor.execute(drop_tables)
    
    # Create tables with exact structure and foreign keys
    create_tables_sql = """
    -- 1. Users table (no dependencies)
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    );
    
    -- 2. Guru table (no dependencies)
    CREATE TABLE IF NOT EXISTS guru (
        id SERIAL PRIMARY KEY,
        guru_name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 3. Scraper tasks table (depends on guru)
    CREATE TABLE IF NOT EXISTS scraper_tasks (
        id SERIAL PRIMARY KEY,
        symbol TEXT NOT NULL,
        guru_id INTEGER REFERENCES guru(id),
        list_type TEXT,
        scrape_type TEXT NOT NULL,
        active BOOLEAN DEFAULT false,
        current_step TEXT DEFAULT 'rule1',
        scrape_status TEXT DEFAULT 'pending',
        retry_count INTEGER DEFAULT 0,
        last_updated_at TIMESTAMP,
        rule1_scraped_at TIMESTAMP,
        stockscore_scraped_at TIMESTAMP,
        last_price_scraped_at TIMESTAMP,
        last_action TEXT,
        per_portfolio TEXT,
        target BOOLEAN DEFAULT false,
        color VARCHAR(10) DEFAULT 'neutral',
        business_description TEXT,
        address TEXT,
        website TEXT,
        ir_phone_number TEXT,
        email_address TEXT,
        year_established INTEGER,
        fiscal_year_end DATE,
        ceo TEXT,
        number_of_employees INTEGER,
        sp TEXT
    );
    
    -- 4. Old stock analysis table (no foreign keys)
    CREATE TABLE IF NOT EXISTS old_stock_analysis (
        id SERIAL PRIMARY KEY,
        date DATE,
        ticker TEXT,
        source TEXT,
        pe NUMERIC,
        dividend TEXT,
        cash_per_share TEXT,
        current_ratio NUMERIC,
        signal_score INTEGER,
        sentiment_score INTEGER,
        screenshot TEXT,
        guru TEXT,
        rule1_score NUMERIC,
        moat_score NUMERIC,
        management_score NUMERIC,
        buy_price TEXT,
        full_name TEXT,
        last_price TEXT,
        last_action TEXT,
        per_portfolio TEXT,
        long_gr TEXT,
        last_gr TEXT,
        per_upside TEXT,
        pbt TEXT
    );
    
    -- 5. Stock analysis table (depends on guru and scraper_tasks)
    CREATE TABLE IF NOT EXISTS stock_analysis (
        id SERIAL PRIMARY KEY,
        ticker_id INTEGER REFERENCES scraper_tasks(id),
        guru_id INTEGER REFERENCES guru(id),
        date TIMESTAMP,
        ticker TEXT,
        source TEXT,
        pe NUMERIC,
        dividend TEXT,
        cash_per_share TEXT,
        current_ratio NUMERIC,
        signal_score INTEGER,
        sentiment_score INTEGER,
        screenshot TEXT,
        rule1_score NUMERIC,
        moat_score NUMERIC,
        management_score NUMERIC,
        buy_price TEXT,
        full_name TEXT,
        last_price TEXT,
        last_action TEXT,
        per_portfolio TEXT,
        long_gr TEXT,
        last_gr TEXT,
        per_upside TEXT,
        pbt TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 6. Guru ticker map table (depends on guru and scraper_tasks)
    CREATE TABLE IF NOT EXISTS guru_ticker_map (
        id SERIAL PRIMARY KEY,
        guru_id INTEGER REFERENCES guru(id),
        scraper_task_id INTEGER REFERENCES scraper_tasks(id),
        per_port TEXT,
        last_act TEXT
    );
    
    -- 7. Comment table (depends on users and scraper_tasks)
    CREATE TABLE IF NOT EXISTS comment (
        id SERIAL PRIMARY KEY,
        comment TEXT NOT NULL,
        user_id INTEGER REFERENCES users(id),
        ticker_id INTEGER REFERENCES scraper_tasks(id),
        color VARCHAR(10) DEFAULT 'neutral',
        date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_tables_sql)
    conn.commit()
    
    print("✅ Tables created with foreign key constraints")
    print("📋 Dependency order: users → guru → scraper_tasks → stock_analysis/guru_ticker_map → comment")
    
    # Verify tables created
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print("✅ Database structure created successfully!")
    print("📊 Tables created:")
    for table in tables:
        print(f"  - {table[0]}")
    
    return len(tables)

def main():
    """Main function"""
    try:
        table_count = create_database_structure()
        print(f"\n🎉 Setup completed: {table_count} tables ready")
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    main()