# Financial Market Data Pipeline
**COMP6265 — Data Integration and Warehousing**  
University of Southampton — Group 1

---

## Overview

A modular end-to-end financial data pipeline that ingests live market data from multiple APIs, applies ETL transformations, stores processed data in a PostgreSQL warehouse, and exposes insights via a Streamlit dashboard.

**Data sources:**
- [Alpha Vantage](https://www.alphavantage.co/) — stocks and forex
- [CoinGecko](https://www.coingecko.com/en/api) — cryptocurrency
- [NewsAPI](https://newsapi.org/) — financial news headlines

---

## Team

| Member | Role | Branch |
|--------|------|--------|
| Akash | APIs & Ingestion | `feature/ingestion-api` |
| Ausaf | ETL Pipeline | `ausaf` |
| Adam | Data Storage & PostgreSQL | `FRONTEND` |
| Mayur | Frontend Dashboard | `FRONTEND` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Data Sources                        │
│  Alpha Vantage (Stocks/Forex)  │  CoinGecko (Crypto)    │
│              NewsAPI (Headlines)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Ingestion Layer (src/ingestion/)        │
│  StockFetcher · ForexFetcher · CryptoFetcher            │
│  Retry logic · Rate limiting · Standardised schema      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Data Lake (Cloudflare R2 / local fallback) │
│              Raw Parquet files                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  ETL Pipeline (src/etl/)                 │
│  Cleaner → Transformer → Validator → Pipeline           │
│  Rolling averages · Volatility · % change               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Warehouse (warehouse/)           │
│  Schema · Load · Query                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Dashboard (React frontend + Flask backend)       │
│  Live prices · Historical charts · News feed            │
│  Deployed via Railway (Docker)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Keycloak (Access Control)                   │
│  Role-based access: User · Analyst · Admin              │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
comp6265-group1-financial-data-pipeline/
├── src/
│   ├── ingestion/
│   │   ├── base.py              # Abstract BaseFetcher
│   │   ├── stock_fetcher.py     # Alpha Vantage — equities
│   │   ├── forex_fetcher.py     # Alpha Vantage — FX_DAILY
│   │   ├── crypto_fetcher.py    # CoinGecko — crypto OHLC
│   │   ├── news_fetcher.py      # NewsAPI — financial headlines
│   │   ├── config.py            # API keys and symbol config
│   │   ├── utils.py             # Retry, rate limiting, helpers
│   │   └── tests/               # Unit tests (unittest + mock)
│   ├── etl/
│   │   ├── transform.py         # Rolling avg, volatility, % change
│   │   └── __init__.py
│   ├── orchestration/
│   │   └── scheduler.py         # Runs the full pipeline end-to-end
│   ├── storage/
│   │   ├── lake_writer.py       # Writes raw data to R2 or local fallback
│   │   └── lake_reader.py       # Reads from data lake
│   ├── warehouse/
│   │   ├── schema.py            # PostgreSQL table definitions
│   │   ├── load.py              # Bulk insert cleaned data
│   │   ├── query.py             # Parameterised query interface
│   │   └── db.py                # DB connection setup
│   └── dashboard/
│       ├── Dockerfile           # Multi-stage build (Node → Python)
│       ├── backend/
│       │   └── app.py           # Flask API (serves data + JWT auth)
│       └── frontend/
│           └── src/
│               ├── App.jsx
│               ├── keycloak.js  # Keycloak OIDC integration
│               ├── components/  # StockPanel, ForexPanel, CryptoPanel, NewsPanel, AuditLogPanel
│               └── services/
│                   └── api.js
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/adam-a-k/comp6265-group1-financial-data-pipeline.git
cd comp6265-group1-financial-data-pipeline
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
ALPHA_VANTAGE_KEY=your_key_here
NEWS_API_KEY=your_key_here

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=financial_pipeline
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Cloudflare R2 (optional — pipeline falls back to local if unset)
R2_ACCOUNT_ID=
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_BUCKET=
```

> **Note:** CoinGecko does not require an API key. Alpha Vantage free tier allows 25 requests/day.

### 5. Set up the PostgreSQL database

```bash
python warehouse/schema.py
```

---

## Running the Pipeline

### Full pipeline (scheduler)

```bash
python src/orchestration/scheduler.py
```

### Dashboard (local)

```bash
# Backend — Flask API
cd src/dashboard
pip install -r requirements.txt
python backend/app.py

# Frontend — React (separate terminal)
cd src/dashboard/frontend
npm install --legacy-peer-deps
npm run dev
```

Open `http://localhost:5173` in your browser.

### Dashboard (Docker)

```bash
cd src/dashboard
docker build -t financial-dashboard .
docker run -p 8080:8080 --env-file ../../.env financial-dashboard
```

The dashboard is deployed to **Railway** via Docker (https://reasonable-abundance-production-b4d5.up.railway.app/). The Dockerfile performs a multi-stage build: Node.js compiles the React frontend, then Python serves it via Flask.

### Live API smoke test

```bash
python quick_test.py
```

---

## Running Tests

```bash
python -m pytest src/ingestion/tests/ -v
```

**44 unit tests** covering all three fetchers, retry logic, rate limiting, and schema standardisation. All tests use `unittest.mock` — no real API calls are made.

---

## Key Technical Features

- **Standardised schema** — all three ingestion sources output a consistent DataFrame (`symbol`, `date`, `open`, `high`, `low`, `close`, `volume`) before entering the ETL
- **Retry with backoff** — transient API failures are retried automatically
- **Rate limiting** — prevents Alpha Vantage free tier from being exceeded
- **Parameterised SQL** — all warehouse queries use `%s` placeholders to prevent injection
- **Local data lake fallback** — if R2 credentials are absent, raw data is written to `data_lake/` locally, keeping the pipeline runnable without cloud access
- **Non-trivial transformations** — ETL computes 7-day rolling averages, annualised volatility, and percentage change per symbol
- **Role-based access control** — Keycloak enforces three access tiers: `User` (read-only dashboard), `Analyst` (query access), `Admin` (full pipeline control)

---

## Dependencies

Key packages (see `requirements.txt` for full list):

| Package | Purpose |
|---------|---------|
| `requests` | HTTP API calls |
| `pandas` | Data manipulation |
| `psycopg2` | PostgreSQL connector |
| `flask` | Backend API server |
| `flask-cors` | Cross-origin requests (React ↔ Flask) |
| `python-jose` | JWT validation for Keycloak tokens |
| `boto3` | Cloudflare R2 (S3-compatible) |
| `python-dotenv` | Environment variable loading |
| `pytest` | Test runner |
| `python-keycloak` | Keycloak OIDC integration |

---

## API Keys

| API | Free Tier | Sign Up |
|-----|-----------|---------|
| Alpha Vantage | 25 req/day | https://www.alphavantage.co/support/#api-key |
| NewsAPI | 100 req/day | https://newsapi.org/register |
| CoinGecko | No key needed | — |

---

## Module: COMP6265 — Data Integration and Warehousing  
**University of Southampton · Academic Year 2025/26**
