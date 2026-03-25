CREATE TABLE IF NOT EXISTS stock_prices (
    timestamp TIMESTAMP,
    symbol VARCHAR(10),
    price_usd FLOAT
);

CREATE TABLE IF NOT EXISTS forex_rates (
    timestamp TIMESTAMP,
    pair VARCHAR(10),
    rate FLOAT
);

CREATE TABLE IF NOT EXISTS news_sentiment (
    timestamp TIMESTAMP,
    symbol VARCHAR(10),
    sentiment FLOAT
);