import pandas as pd
from pathlib import Path

DATA_LAKE = Path("data_lake/stocks")


def load_raw():

    files = list(DATA_LAKE.glob("*.json"))

    df_list = []

    for file in files:
        df = pd.read_json(file, lines=True)
        df_list.append(df)

    return pd.concat(df_list)


def clean_data(df):

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df.rename(columns={
        "price": "price_usd"
    }, inplace=True)

    return df


def transform():

    raw = load_raw()

    clean = clean_data(raw)

    return clean


if __name__ == "__main__":

    df = transform()
    print(df.head())