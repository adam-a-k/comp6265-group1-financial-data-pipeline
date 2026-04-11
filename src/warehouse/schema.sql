DROP TABLE IF EXISTS stock_prices;
CREATE TABLE IF NOT EXISTS stock_prices (
    timestamp TIMESTAMP,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    symbol VARCHAR(10),
    source VARCHAR(10)
);

DROP TABLE IF EXISTS forex_rates;
CREATE TABLE IF NOT EXISTS forex_rates (
    timestamp TIMESTAMP,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    symbol VARCHAR(10),
    source VARCHAR(10)
);

DROP TABLE IF EXISTS crypto_rates;
CREATE TABLE IF NOT EXISTS crypto_rates (
    timestamp TIMESTAMP,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    symbol VARCHAR(10),
    source VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS news_sentiment (
    timestamp TIMESTAMP,
    symbol VARCHAR(10),
    sentiment FLOAT
);