import pandas as pd
from src.warehouse.db import engine
from src.etl.transform import transform


def load_to_db():

    df = transform()

    df.to_sql(
        "stock_prices",
        engine,
        if_exists="append",
        index=False
    )


if __name__ == "__main__":

    load_to_db()