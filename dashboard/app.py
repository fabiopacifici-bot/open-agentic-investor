"""
dashboard/app.py — Flask local dashboard for open-agentic-investor.

Run: python -m dashboard.app (from repo root)
URL: http://localhost:5001
Data: ~/Documents/Investments/portfolio.db
"""

import os
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from flask import Flask, jsonify, render_template, request

DATA_DIR = Path(os.path.expanduser("~/Documents/Investments"))
DB_PATH = DATA_DIR / "portfolio.db"

app = Flask(__name__)


def get_db():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def range_to_cutoff(range_str: str) -> str | None:
    now = datetime.now(timezone.utc)
    if range_str == "day":
        return (now - timedelta(days=1)).isoformat()
    elif range_str == "week":
        return (now - timedelta(weeks=1)).isoformat()
    elif range_str == "month":
        return (now - timedelta(days=30)).isoformat()
    return None  # all


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/snapshots")
def api_snapshots():
    range_str = request.args.get("range", "week")
    cutoff = range_to_cutoff(range_str)
    conn = get_db()
    if not conn:
        return jsonify([])
    query = "SELECT timestamp, total_value, pnl, pnl_pct FROM snapshots"
    params = []
    if cutoff:
        query += " WHERE timestamp >= ?"
        params.append(cutoff)
    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/positions/latest")
def api_positions_latest():
    conn = get_db()
    if not conn:
        return jsonify([])
    snap = conn.execute("SELECT id FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
    if not snap:
        conn.close()
        return jsonify([])
    rows = conn.execute(
        "SELECT * FROM positions WHERE snapshot_id=? ORDER BY value DESC", (snap["id"],)
    ).fetchall()
    # Get latest recommendation per ticker
    rec_rows = conn.execute(
        "SELECT ticker, action, reason FROM recommendations ORDER BY id DESC LIMIT 200"
    ).fetchall()
    recs = {}
    for r in rec_rows:
        if r["ticker"] not in recs:
            recs[r["ticker"]] = {"action": r["action"], "reason": r["reason"]}
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["recommendation"] = recs.get(d["ticker"], {"action": "HOLD", "reason": ""})
        result.append(d)
    return jsonify(result)


@app.route("/api/recommendations")
def api_recommendations():
    conn = get_db()
    if not conn:
        return jsonify([])
    rows = conn.execute(
        "SELECT * FROM recommendations ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
