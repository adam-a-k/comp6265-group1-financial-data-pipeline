import pandas as pd
from src.warehouse.db import engine

def get_stock_history(symbol="AAPL"):

    query = f"""
    SELECT *
    FROM stock_prices
    WHERE symbol = '{symbol}'
    ORDER BY timestamp
    """

    return pd.read_sql(query, engine)