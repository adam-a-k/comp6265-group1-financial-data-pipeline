from sqlalchemy import create_engine

DB_URI = "postgresql://user:password@localhost:5432/market_data"

engine = create_engine(DB_URI)