# FinPulse Dashboard

Full-stack financial dashboard — React + Vite frontend, Flask backend.

## Project Structure

```
project/
├── backend/
│   ├── app.py            ← Flask API (stocks, forex, news)
│   └── requirements.txt
├── src/
│   ├── components/
│   │   ├── StockPanel.jsx
│   │   ├── ForexPanel.jsx
│   │   └── NewsPanel.jsx
│   ├── hooks/
│   │   └── usePolling.js  ← auto-refreshes data every 30s
│   ├── services/
│   │   └── api.js         ← all API calls in one place
│   ├── App.jsx
│   ├── App.css
│   └── main.jsx
├── index.html
├── package.json
└── vite.config.js         ← proxies /api → localhost:8000
```

## Setup (run TWO terminals)

### Terminal 1 — Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
# Flask runs on http://localhost:8000
```

### Terminal 2 — Frontend
```bash
npm install
npm run dev
# React runs on http://localhost:3000
```

Open http://localhost:3000

## Connecting to your real data pipeline

In `backend/app.py`, each endpoint has a comment showing where to
plug in your real data source. For example, in `get_stocks()`:

```python
@app.route("/api/stocks")
def get_stocks():
    # Replace this with a real query, e.g.:
    # from warehouse.query import get_latest_prices
    # return jsonify(get_latest_prices())
```

Your pipeline flow:
```
forex_api.py / stocks_api.py / news_api.py
        ↓
    transform.py  (ETL)
        ↓
    lake_writer.py  (Storage)
        ↓
    warehouse/  (cleaned data)
        ↓
    app.py  (Flask API reads from here)
        ↓
    React frontend  (calls /api/*)
```

## Data refresh
- Stocks and Forex refresh every **30 seconds** (configurable in usePolling.js)
- News refreshes every **60 seconds**
