import schedule
import time

from src.ingestion.stocks_api import fetch_stock_price, store_raw
from src.warehouse.load import load_to_db


def ingest():

    record = fetch_stock_price()
    store_raw(record)


def etl():

    load_to_db()


schedule.every(5).minutes.do(ingest)
schedule.every().hour.do(etl)

while True:

    schedule.run_pending()
    time.sleep(1)