import pandas as pd
from src.warehouse.db import engine
from src.etl.transform import transform_stocks, transform_crypto, transform_forex


def load_to_db(df, table, transform_function):

    df = transform_function(df)
    print(df)
    # df.to_sql(
    #     table,
    #     engine,
    #     if_exists="append",
    #     index=False
    # )