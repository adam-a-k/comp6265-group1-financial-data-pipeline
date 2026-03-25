import streamlit as st
from src.warehouse.query import get_stock_history

st.title("Financial Market Dashboard")

symbol = st.selectbox(
    "Select stock",
    ["AAPL", "MSFT", "GOOG"]
)

df = get_stock_history(symbol)

st.line_chart(
    df.set_index("timestamp")["price_usd"]
)