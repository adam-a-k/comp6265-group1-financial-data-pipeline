from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import text, create_engine
#from src.warehouse.db import engine
import random
import datetime
import os

DB_URI = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DB_URI)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, '..', 'dist')

app = Flask(__name__, static_folder=DIST_DIR, static_url_path='')
#app = Flask(__name__, static_folder=os.path.join('..', 'dist'), static_url_path='')
CORS(app)

# ── Serve React frontend ──
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# ── STOCKS ──
@app.route("/api/stocks")
def get_stocks():
    # symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA"]
    # base_prices = {"AAPL": 189, "GOOGL": 141, "MSFT": 378, "AMZN": 185, "TSLA": 177, "NVDA": 875}
    # stocks = []
    # for sym in symbols:
    #     base = base_prices[sym]
    #     change_pct = round(random.uniform(-3.5, 3.5), 2)
    #     price = round(base * (1 + change_pct / 100), 2)
    #     stocks.append({
    #         "symbol": sym,
    #         "price": price,
    #         "change": change_pct,
    #         "volume": random.randint(10_000_000, 90_000_000),
    #         "history": [round(base * (1 + random.uniform(-0.05, 0.05)), 2) for _ in range(30)]
    #     })
    # return jsonify(stocks)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM stock_prices ORDER BY timestamp DESC"))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        row["timestamp"] = row["timestamp"].isoformat()
    return jsonify(rows)

# ── FOREX ──
@app.route("/api/forex")
def get_forex():
    # pairs = [
    #     {"pair": "EUR/USD", "base": 1.085},
    #     {"pair": "GBP/USD", "base": 1.271},
    #     {"pair": "USD/JPY", "base": 149.5},
    #     {"pair": "AUD/USD", "base": 0.652},
    #     {"pair": "USD/CAD", "base": 1.362},
    #     {"pair": "USD/INR", "base": 83.1},
    # ]
    # result = []
    # for p in pairs:
    #     change = round(random.uniform(-0.8, 0.8), 4)
    #     result.append({
    #         "pair": p["pair"],
    #         "rate": round(p["base"] + change * 0.01, 4),
    #         "change": round(change, 4),
    #         "change_pct": round(change / p["base"] * 100, 3),
    #         "history": [round(p["base"] + random.uniform(-0.02, 0.02), 4) for _ in range(30)]
    #     })
    # return jsonify(result)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM forex_rates ORDER BY timestamp DESC"))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        row["timestamp"] = row["timestamp"].isoformat()
    return jsonify(rows)

#Crypto
@app.route("/api/crypto")
def get_crypto():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM crypto_rates ORDER BY timestamp DESC"))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        row["timestamp"] = row["timestamp"].isoformat()
    return jsonify(rows)

# ── NEWS ──
@app.route("/api/news")
def get_news():
    headlines = [
        {"title": "Fed holds rates steady amid inflation concerns", "source": "Reuters", "sentiment": "neutral", "category": "macro"},
        {"title": "NVDA surges 6% on strong AI chip demand forecast", "source": "Bloomberg", "sentiment": "positive", "category": "tech"},
        {"title": "EUR/USD falls as ECB signals rate cut timeline", "source": "FT", "sentiment": "negative", "category": "forex"},
        {"title": "Apple announces record buyback programme", "source": "CNBC", "sentiment": "positive", "category": "stocks"},
        {"title": "Oil prices dip on weaker demand outlook from China", "source": "Reuters", "sentiment": "negative", "category": "commodities"},
        {"title": "US jobs data beats expectations, market rallies", "source": "WSJ", "sentiment": "positive", "category": "macro"},
        {"title": "Tesla faces recall on autopilot software update", "source": "Bloomberg", "sentiment": "negative", "category": "stocks"},
        {"title": "Bank of Japan hints at end of negative rate policy", "source": "Nikkei", "sentiment": "neutral", "category": "forex"},
    ]
    now = datetime.datetime.utcnow()
    result = []
    for i, h in enumerate(headlines):
        result.append({
            **h,
            "id": i + 1,
            "timestamp": (now - datetime.timedelta(minutes=i * 18)).strftime("%H:%M"),
            "ago": f"{i * 18}m ago" if i > 0 else "Just now"
        })
    return jsonify(result)

@app.route('/health')
def health():
    return 'ok'

@app.route('/debug')
def debug():
    return {
        'static_folder': app.static_folder,
        'exists': os.path.exists(app.static_folder),
        'index_exists': os.path.exists(os.path.join(app.static_folder, 'index.html'))
    }

if __name__ == "__main__":
    app.run(debug=True, port=8000)