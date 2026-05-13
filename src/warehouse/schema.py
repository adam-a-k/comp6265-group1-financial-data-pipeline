SCHEMA_SQL = """
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
CREATE TABLE IF NOT EXISTS crypto_rates (
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
CREATE TABLE IF NOT EXISTS news (
    id          SERIAL PRIMARY KEY,
    timestamp   TIMESTAMPTZ NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    source      TEXT        NOT NULL,
    title       TEXT,
    description TEXT,
    url         TEXT,
    publisher   TEXT,
    CONSTRAINT uq_news_url UNIQUE (url)
);
"""