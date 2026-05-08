import pandas as pd
from src.warehouse.db import engine
from src.etl.transform import transform_stocks, transform_crypto, transform_forex


def load_to_db(df):

    df = transform_stocks(df)

    df.to_sql(
        "stock_prices",
        engine,
        if_exists="append",
        index=False
    )


if __name__ == "__main__":

    load_to_db()