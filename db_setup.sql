-- Clean database and create proper FK/PK relations

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

-- Create scraper_tasks table with FK to guru
CREATE TABLE scraper_tasks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    guru_id INTEGER REFERENCES guru(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create stock_analysis table with FK to scraper_tasks
CREATE TABLE stock_analysis (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER NOT NULL REFERENCES scraper_tasks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    source VARCHAR(50) NOT NULL,
    rule1_score NUMERIC,
    management_score NUMERIC,
    moat_score NUMERIC,
    buy_price NUMERIC,
    last_price NUMERIC,
    percentage_upside NUMERIC,
    dividend NUMERIC,
    cash_per_share NUMERIC,
    signal_score INTEGER,
    sentiment_score INTEGER,
    screenshot_url TEXT,
    pbt NUMERIC,
    last_gr NUMERIC,
    long_gr NUMERIC,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker_id, date, source)
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

-- Insert default data
INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin');
INSERT INTO guru (guru_name, description) VALUES ('default', 'Default guru for general tickers');
CREATE INDEX idx_comment_user_id ON comment(user_id);
CREATE INDEX idx_comment_ticker_id ON comment(ticker_id);
CREATE INDEX idx_scraper_tasks_guru_id ON scraper_tasks(guru_id);