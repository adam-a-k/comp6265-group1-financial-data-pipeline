import schedule
import time
from datetime import datetime, timezone
from src.ingestion import StockFetcher, ForexFetcher, CryptoFetcher
#from src.ingestion.stocks_api import fetch_stock_price, store_raw
from src.warehouse.load import load_to_db
from src.storage.lake_writer import write_to_lake

def ingest():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    for symbol in ["AAPL", "GOOGL", "MSFT"]:
        stocks_df = StockFetcher().fetch(symbol)
        write_to_lake(stocks_df, f"stocks/{symbol}/{ts}.csv")

    for from_sym, to_sym in [("USD", "EUR"), ("USD", "GBP")]:
        forex_df = ForexFetcher().fetch(from_symbol=from_sym, to_symbol=to_sym)
        write_to_lake(forex_df, f"forex/{from_sym}{to_sym}/{ts}.csv")

    for coin in ["bitcoin", "ethereum"]:
        crypto_df = CryptoFetcher().fetch(coin, vs_currency="usd", days=30)
        write_to_lake(crypto_df, f"crypto/{coin}/{ts}.csv")

    return stocks_df, forex_df, crypto_df

def etl(df):

    load_to_db(df)


stocks_df, forex_df, crypto_df = ingest()
#etl(stocks_df)

# schedule.every(5).minutes.do(ingest)
# schedule.every().hour.do(etl)


# while True:
#     pass
#     schedule.run_pending()
#     time.sleep(1)