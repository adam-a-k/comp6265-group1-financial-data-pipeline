from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from sqlalchemy import text, create_engine
#from src.warehouse.db import engine
import random
import datetime
import os
from jose import jwt

DB_URI = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DB_URI)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'dist')

app = Flask(__name__, static_folder=DIST_DIR, static_url_path='')
#app = Flask(__name__, static_folder=os.path.join('..', 'dist'), static_url_path='')
CORS(app)

def log_action(action, resource, resource_id=None, user_id=None, detail=None):
    from flask import request as freq
    import json
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO audit_logs (action, resource, resource_id, user_id, ip_address, detail)
            VALUES (:action, :resource, :resource_id, :user_id, :ip, :detail)
        """), {
            "action": action, "resource": resource,
            "resource_id": str(resource_id) if resource_id else None,
            "user_id": user_id,
            "ip": freq.remote_addr,
            "detail": json.dumps(detail) if detail else None
        })
        conn.commit()

def get_user_from_token():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ')[1]
    try:
        decoded = jwt.decode(
            token,
            key='',
            algorithms=["RS256"],
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_exp": False,
            }
        )
        return decoded.get('preferred_username')
    except Exception as e:
        print("JWT ERROR:", e)
        return None

def get_user_roles():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return []
    token = auth.split(' ')[1]
    try:
        decoded = jwt.decode(
            token, key='', algorithms=["RS256"],
            options={"verify_signature": False, "verify_aud": False, "verify_exp": False}
        )
        roles = decoded.get('realm_access', {}).get('roles', [])
        print(roles)
        return roles
    except Exception as e:
        print("ROLES ERROR: ", e)
        return []


# ── Serve React frontend ──
@app.route('/')
def serve():
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
    log_action('READ', 'stock_prices', user_id=get_user_from_token())
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
    log_action('READ', 'forex_rates', user_id=get_user_from_token())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM forex_rates ORDER BY timestamp DESC"))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        row["timestamp"] = row["timestamp"].isoformat()
    return jsonify(rows)

#Crypto
@app.route("/api/crypto")
def get_crypto():
    log_action('READ', 'crypto_rates', user_id=get_user_from_token())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM crypto_rates ORDER BY timestamp DESC"))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        row["timestamp"] = row["timestamp"].isoformat()
    return jsonify(rows)

# ── NEWS ──
@app.route("/api/news")
def get_news():
    # headlines = [
    #     {"title": "Fed holds rates steady amid inflation concerns", "source": "Reuters", "sentiment": "neutral", "category": "macro"},
    #     {"title": "NVDA surges 6% on strong AI chip demand forecast", "source": "Bloomberg", "sentiment": "positive", "category": "tech"},
    #     {"title": "EUR/USD falls as ECB signals rate cut timeline", "source": "FT", "sentiment": "negative", "category": "forex"},
    #     {"title": "Apple announces record buyback programme", "source": "CNBC", "sentiment": "positive", "category": "stocks"},
    #     {"title": "Oil prices dip on weaker demand outlook from China", "source": "Reuters", "sentiment": "negative", "category": "commodities"},
    #     {"title": "US jobs data beats expectations, market rallies", "source": "WSJ", "sentiment": "positive", "category": "macro"},
    #     {"title": "Tesla faces recall on autopilot software update", "source": "Bloomberg", "sentiment": "negative", "category": "stocks"},
    #     {"title": "Bank of Japan hints at end of negative rate policy", "source": "Nikkei", "sentiment": "neutral", "category": "forex"},
    # ]
    # now = datetime.datetime.utcnow()
    # result = []
    # for i, h in enumerate(headlines):
    #     result.append({
    #         **h,
    #         "id": i + 1,
    #         "timestamp": (now - datetime.timedelta(minutes=i * 18)).strftime("%H:%M"),
    #         "ago": f"{i * 18}m ago" if i > 0 else "Just now"
    #     })
    # return jsonify(result)
    log_action('READ', 'news', user_id=get_user_from_token())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM news ORDER BY timestamp DESC LIMIT 20"))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        if row.get("timestamp"):
            row["timestamp"] = row["timestamp"].isoformat()
        if row.get("fetched_at"):
            row["fetched_at"] = row["fetched_at"].isoformat()
    return jsonify(rows)

@app.route('/health')
def health():
    if 'admin' not in get_user_roles():
        return jsonify({"error": "Forbidden"}), 403
    return 'ok'

@app.route('/debug')
def debug():
    if 'admin' not in get_user_roles():
        return jsonify({"error": "Forbidden"}), 403
    return {
        'static_folder': app.static_folder,
        'exists': os.path.exists(app.static_folder),
        'index_exists': os.path.exists(os.path.join(app.static_folder, 'index.html'))
    }

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          SERIAL PRIMARY KEY,
            action      VARCHAR(64)  NOT NULL,
            resource    VARCHAR(128) NOT NULL,
            resource_id VARCHAR(128),
            user_id     VARCHAR(128),
            ip_address  VARCHAR(64),
            detail      TEXT,
            timestamp   TIMESTAMP DEFAULT NOW()
        )
    """))
    conn.commit()

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS source_registry (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(256) NOT NULL,
            source_type VARCHAR(64)  NOT NULL DEFAULT 'REST_API',
            url         TEXT,
            owner       VARCHAR(128),
            status      VARCHAR(32)  NOT NULL DEFAULT 'active',
            registered_at TIMESTAMP  DEFAULT NOW()
        )
    """))
    conn.commit()


@app.route("/api/registry/", methods=["GET"])
def registry_list():
    roles = get_user_roles()
    if not any(r in roles for r in ('analyst', 'admin')):
        return jsonify({"error": "Forbidden"}), 403
    log_action('READ', 'source_registry', user_id=get_user_from_token())
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM source_registry ORDER BY registered_at DESC"
        ))
        result = [dict(r._mapping) for r in rows]
    for row in result:
        if row.get("registered_at"):
            row["registered_at"] = row["registered_at"].isoformat()
    return jsonify(result)

@app.route("/api/registry/", methods=["POST"])
def registry_create():
    if 'admin' not in get_user_roles():
        return jsonify({"error": "Forbidden"}), 403
    log_action('CREATE', 'source_registry', user_id=get_user_from_token())
    data = request.get_json()
    user = get_user_from_token()
    with engine.connect() as conn:
        row = conn.execute(text("""
            INSERT INTO source_registry (name, source_type, url, owner, status)
            VALUES (:name, :source_type, :url, :owner, :status)
            RETURNING *
        """), {
            "name":        data.get("name"),
            "source_type": data.get("source_type", "REST_API"),
            "url":         data.get("url"),
            "owner":       data.get("owner"),
            "status":      data.get("status", "active"),
        }).mappings().one()
        conn.commit()
    log_action('CREATE', 'source_registry', resource_id=row["id"], user_id=user)
    result = dict(row)
    result["registered_at"] = result["registered_at"].isoformat()
    return jsonify(result), 201

@app.route("/api/registry/<int:source_id>", methods=["DELETE"])
def registry_delete(source_id):
    if 'admin' not in get_user_roles():
        return jsonify({"error": "Forbidden"}), 403
    log_action('DELETE', 'source_registry', user_id=get_user_from_token())
    user = get_user_from_token()
    with engine.connect() as conn:
        conn.execute(text(
            "DELETE FROM source_registry WHERE id = :id"
        ), {"id": source_id})
        conn.commit()
    log_action('DELETE', 'source_registry', resource_id=source_id, user_id=user)
    return "", 204

@app.route("/api/registry/<int:source_id>", methods=["PATCH"])
def registry_patch(source_id):
    if 'admin' not in get_user_roles():
        return jsonify({"error": "Forbidden"}), 403
    log_action('UPDATE', 'source_registry', user_id=get_user_from_token())
    data = request.get_json()
    user = get_user_from_token()
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE source_registry SET status = :status WHERE id = :id
        """), {"status": data.get("status"), "id": source_id})
        conn.commit()
    log_action('UPDATE', 'source_registry', resource_id=source_id, user_id=user, detail=data)
    return "", 204

@app.route("/api/audit-logs")
def get_audit_logs():
    if 'admin' not in get_user_roles():
        return jsonify({"error": "Forbidden"}), 403
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 200"
        ))
        rows = [dict(r._mapping) for r in result]
    for row in rows:
        row["timestamp"] = row["timestamp"].isoformat()
    return jsonify(rows)


@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')





if __name__ == "__main__":
    app.run(debug=True, port=8000)