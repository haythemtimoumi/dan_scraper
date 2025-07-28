-- Clean database and recreate with correct structure

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS comment CASCADE;
DROP TABLE IF EXISTS stock_analysis CASCADE;
DROP TABLE IF EXISTS scraper_tasks CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS guru CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create guru table
CREATE TABLE guru (
    id SERIAL PRIMARY KEY,
    guru_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create scraper_tasks table with correct structure
CREATE TABLE scraper_tasks ( 
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    guru_name TEXT,
    list_type TEXT,
    scrape_type TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    current_step TEXT DEFAULT 'rule1',
    scrape_status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP,
    rule1_scraped_at TIMESTAMP,
    stockscore_scraped_at TIMESTAMP,
    last_price_scraped_at TIMESTAMP,
    last_action TEXT,
    per_portfolio TEXT,
    UNIQUE(symbol, guru_name, list_type)
);

-- Create stock_analysis table with original structure (no FK)
CREATE TABLE stock_analysis (
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

-- Create comment table
CREATE TABLE comment (
    id SERIAL PRIMARY KEY,
    comment TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker_id INTEGER NOT NULL,
    color VARCHAR(10) DEFAULT 'neutral' CHECK (color IN ('red', 'yellow', 'green', 'neutral')),
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_comment_user_id ON comment(user_id);
CREATE INDEX idx_comment_ticker_id ON comment(ticker_id);

-- Insert default data
INSERT INTO users (username, password, role) VALUES 
    ('admin', 'admin123', 'admin'),
    ('admindan', '$2y$10$gGp5Xjy0sRUSxkau.qczAOR5r8wJLDQr2S5clZT7y7xc22JVP/h1q', 'admin'),
    ('user1', '$2y$10$gGp5Xjy0sRUSxkau.qczAOR5r8wJLDQr2S5clZT7y7xc22JVP/h1q', 'user');

INSERT INTO guru (guru_name, description) VALUES ('default', 'Default guru for general tickers');