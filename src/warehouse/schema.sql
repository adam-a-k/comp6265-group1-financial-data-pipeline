DROP TABLE IF EXISTS stock_prices;
CREATE TABLE IF NOT EXISTS stock_prices (
    timestamp       TIMESTAMPTZ     NOT NULL,
    open            FLOAT,
    high            FLOAT,
    low             FLOAT,
    price           FLOAT,
    volume          FLOAT,
    symbol          TEXT            NOT NULL,
    source          TEXT            NOT NULL,
    rolling_avg_7d  FLOAT,
    price_change_pct FLOAT
);

DROP TABLE IF EXISTS forex_rates;
CREATE TABLE IF NOT EXISTS forex_rates (
    timestamp       TIMESTAMPTZ     NOT NULL,
    open            FLOAT,
    high            FLOAT,
    low             FLOAT,
    price           FLOAT,
    volume          FLOAT,
    symbol          TEXT            NOT NULL,
    source          TEXT            NOT NULL,
    rolling_avg_7d  FLOAT,
    price_change_pct FLOAT
);

DROP TABLE IF EXISTS crypto_rates;
CREATE TABLE IF NOT EXISTS crypto_rates (
    timestamp       TIMESTAMPTZ     NOT NULL,
    open            FLOAT,
    high            FLOAT,
    low             FLOAT,
    price           FLOAT,
    symbol          TEXT            NOT NULL,
    source          TEXT            NOT NULL,
    rolling_avg_7d  FLOAT,
    price_change_pct FLOAT
);

DROP TABLE IF EXISTS news;
CREATE TABLE IF NOT EXISTS news (
    timestamp TIMESTAMP,
    symbol VARCHAR(10),
    sentiment FLOAT
);