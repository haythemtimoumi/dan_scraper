-- Final database structure with proper FK relations

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS comment CASCADE;
DROP TABLE IF EXISTS stock_analysis CASCADE;
DROP TABLE IF EXISTS scraper_tasks CASCADE;
DROP TABLE IF EXISTS guru CASCADE;

-- Keep users table as is

-- Create guru table
CREATE TABLE guru (
    id SERIAL PRIMARY KEY,
    guru_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create scraper_tasks table with FK to guru
CREATE TABLE scraper_tasks ( 
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    guru_id INTEGER REFERENCES guru(id),
    list_type TEXT,
    scrape_type TEXT NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    current_step TEXT DEFAULT 'rule1',
    scrape_status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP,
    rule1_scraped_at TIMESTAMP,
    stockscore_scraped_at TIMESTAMP,
    last_price_scraped_at TIMESTAMP,
    last_action TEXT,
    per_portfolio TEXT,
    UNIQUE(symbol, guru_id, list_type)
);

-- Create stock_analysis table with FK to scraper_tasks and guru
CREATE TABLE stock_analysis (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER REFERENCES scraper_tasks(id) ON DELETE CASCADE,
    guru_id INTEGER REFERENCES guru(id),
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

-- Create comment table with FK to users and scraper_tasks
CREATE TABLE comment (
    id SERIAL PRIMARY KEY,
    comment TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker_id INTEGER NOT NULL REFERENCES scraper_tasks(id) ON DELETE CASCADE,
    color VARCHAR(10) DEFAULT 'neutral' CHECK (color IN ('red', 'yellow', 'green', 'neutral')),
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_scraper_tasks_guru_id ON scraper_tasks(guru_id);
CREATE INDEX idx_stock_analysis_ticker_id ON stock_analysis(ticker_id);
CREATE INDEX idx_stock_analysis_guru_id ON stock_analysis(guru_id);
CREATE INDEX idx_comment_user_id ON comment(user_id);
CREATE INDEX idx_comment_ticker_id ON comment(ticker_id);

-- Insert default guru
INSERT INTO guru (guru_name, description) VALUES ('default', 'Default guru for general tickers');