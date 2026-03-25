import requests
import json
from datetime import datetime
from pathlib import Path

DATA_LAKE = Path("data_lake/stocks")

def fetch_stock_price(symbol="AAPL"):

    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"

    r = requests.get(url)
    data = r.json()

    price = data["quoteResponse"]["result"][0]["regularMarketPrice"]

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "price": price
    }

    return record


def store_raw(record):

    filename = DATA_LAKE / f"{datetime.utcnow().date()}.json"

    with open(filename, "a") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":

    record = fetch_stock_price()
    store_raw(record)