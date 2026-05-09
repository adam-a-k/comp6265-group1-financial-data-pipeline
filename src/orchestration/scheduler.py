import logging
from datetime import datetime, timezone
from sqlalchemy import text
from src.ingestion import StockFetcher, ForexFetcher, CryptoFetcher
from src.warehouse.load import load_to_db
from src.etl.transform import transform_stocks, transform_crypto, transform_forex
from src.storage.lake_writer import write_to_lake
from src.storage.lake_reader import read_from_lake, list_lake_files
from src.warehouse.db import engine
from src.warehouse.schema import SCHEMA_SQL
logger = logging.getLogger(__name__)

def init_db():
    # with open("schema.sql", "r") as f:
    #     sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(SCHEMA_SQL))
        conn.commit()

def ingest():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    # for symbol in ["AAPL", "GOOGL", "MSFT"]:
    #     stocks_df = StockFetcher().fetch(symbol)
    #     write_to_lake(stocks_df, f"stocks/{symbol}/{ts}.csv")

    # for from_sym, to_sym in [("USD", "EUR"), ("USD", "GBP")]:
    #     forex_df = ForexFetcher().fetch(from_symbol=from_sym, to_symbol=to_sym)
    #     write_to_lake(forex_df, f"forex/{from_sym}{to_sym}/{ts}.csv")

    # for coin in ["bitcoin", "ethereum"]:
    #     crypto_df = CryptoFetcher().fetch(coin, vs_currency="usd", days=30)
    #     write_to_lake(crypto_df, f"crypto/{coin}/{ts}.csv")

    #Loop through different types of each financial data, fetch data then write to data lake
    #Try/Excepts added to avoid error on API rate limits
    for symbol in ["AAPL", "GOOGL", "MSFT"]:
        try:
            stocks_df = StockFetcher().fetch(symbol)
            write_to_lake(stocks_df, f"stocks/{symbol}/{ts}.csv")
        except Exception as e:
            logger.warning(f"Skipping stocks/{symbol}: {e}")

    for from_sym, to_sym in [("USD", "EUR"), ("USD", "GBP")]:
        try:
            forex_df = ForexFetcher().fetch(from_symbol=from_sym, to_symbol=to_sym)
            write_to_lake(forex_df, f"forex/{from_sym}{to_sym}/{ts}.csv")
        except Exception as e:
            logger.warning(f"Skipping forex/{from_sym}{to_sym}: {e}")

    for coin in ["bitcoin", "ethereum"]:
        try:
            crypto_df = CryptoFetcher().fetch(coin, vs_currency="usd", days=30)
            write_to_lake(crypto_df, f"crypto/{coin}/{ts}.csv")
        except Exception as e:
            logger.warning(f"Skipping crypto/{coin}: {e}")

    #return stocks_df, forex_df, crypto_df
    return ts

def etl(ts):
    for symbol in ["AAPL", "GOOGL", "MSFT"]:
        try:
            stocks_df = read_from_lake(f"stocks/{symbol}/{ts}.csv")
            print(stocks_df)
            load_to_db(stocks_df, table="stock_prices", transform_function=transform_stocks)
        except Exception as e:
            logger.warning(f"Skipping stocks/{symbol}: {e}")

    for from_sym, to_sym in [("USD", "EUR"), ("USD", "GBP")]:
        try:
            forex_df = read_from_lake(f"forex/{from_sym}{to_sym}/{ts}.csv")
            print(forex_df)
            load_to_db(forex_df, table="forex_rates", transform_function=transform_forex)
        except Exception as e:
            logger.warning(f"Skipping forex/{from_sym}{to_sym}: {e}")

    for coin in ["bitcoin", "ethereum"]:
        try:
            crypto_df = read_from_lake(f"crypto/{coin}/{ts}.csv")
            print(crypto_df)
            load_to_db(crypto_df, table="crypto_rates", transform_function=transform_crypto)
        except Exception as e:
            logger.warning(f"Skipping crypto/{coin}: {e}")



#stocks_df, forex_df, crypto_df = ingest()
#ingest()
#print(stocks_df)
#etl(stocks_df)

#print(list_lake_files("financial-data-lake/stocks/AAPL"))
#print(read_from_lake("financial-data-lake/stocks/AAPL/20260429T171457.csv"))

#Initialise database
init_db()
#Ingest data from API fetcher to send to data lake, return timestamp value
ts = ingest()
#Use this timestamp value to then extract the recently uploaded raw data from data lake, put into ETL
etl(ts)


# schedule.every(5).minutes.do(ingest)
# schedule.every().hour.do(etl)


# while True:
#     pass
#     schedule.run_pending()
#     time.sleep(1)