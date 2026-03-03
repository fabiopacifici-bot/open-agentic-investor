"""
snapshot.py — Fetch live portfolio data and store to SQLite.

Run: python -m scripts.snapshot (from repo root)
Data stored at: ~/Documents/Investments/portfolio.db
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import json

from credential_handler import load_environment as load_credentials
from scripts.fetch_prices import fetch_portfolio_data
from scripts.fetch_account_info import fetch_account_info
from scripts.portfolio_manager import analyze_portfolio
from utils.logger import logger

DATA_DIR = Path(os.path.expanduser("~/Documents/Investments"))
DB_PATH = DATA_DIR / "portfolio.db"
LOG_VALIDATION = DATA_DIR / "logs" / "snapshot_validation.log"


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total_value REAL,
            cash REAL,
            invested REAL,
            pnl REAL,
            pnl_pct REAL
        );
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            ticker TEXT,
            quantity REAL,
            avg_price REAL,
            current_price REAL,
            value REAL,
            pnl REAL,
            pnl_pct REAL,
            volume INTEGER,
            FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            timestamp TEXT,
            ticker TEXT,
            action TEXT,
            reason TEXT,
            price REAL,
            FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
        );
        CREATE INDEX IF NOT EXISTS idx_recommendations_snapshot ON recommendations(snapshot_id);
    """)
    conn.commit()


def validate_position(pos: dict) -> tuple[bool, str]:
    """Return (True, "") if valid, else (False, reason)."""
    # ticker optional but include for logging
    ticker = pos.get("ticker")

    # current_price
    cp_raw = pos.get("currentPrice")
    if cp_raw is None:
        return False, "current_price is None"
    try:
        cp = float(cp_raw)
    except Exception:
        return False, f"current_price not a number: {cp_raw!r}"

    # quantity
    q_raw = pos.get("quantity")
    if q_raw is None:
        return False, "quantity is None"
    try:
        q = float(q_raw)
    except Exception:
        return False, f"quantity not a number: {q_raw!r}"

    # valid (also allow zero quantity? treat zero as valid but it'll have zero value)
    return True, ""


def _append_validation_log(timestamp: str, total_received: int, total_saved: int, total_dropped: int):
    try:
        LOG_VALIDATION.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_VALIDATION, "a", encoding="utf-8") as f:
            f.write(f"{timestamp}\t{total_received}\t{total_saved}\t{total_dropped}\n")
    except Exception as e:
        logger.error(f"Failed to write validation log: {e}")


def run_snapshot():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    load_credentials()

    logger.info(f"Connecting to DB at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Fetch account info
    try:
        account = fetch_account_info()
    except Exception as e:
        logger.error(f"Failed to fetch account info: {e}")
        account = {}

    total_value = account.get("total", 0.0) or 0.0
    cash = account.get("free", 0.0) or 0.0
    invested = account.get("invested", 0.0) or 0.0
    pnl = account.get("result", 0.0) or 0.0
    pnl_pct = (pnl / invested * 100) if invested else 0.0

    ts = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO snapshots (timestamp, total_value, cash, invested, pnl, pnl_pct) VALUES (?,?,?,?,?,?)",
        (ts, total_value, cash, invested, pnl, pnl_pct)
    )
    snapshot_id = cur.lastrowid
    conn.commit()
    logger.info(f"Snapshot {snapshot_id} saved — total={total_value:.2f}, pnl={pnl:.2f} ({pnl_pct:.2f}%)")

    # Fetch positions
    try:
        raw_positions = fetch_portfolio_data()
    except Exception as e:
        logger.error(f"Failed to fetch portfolio data: {e}")
        raw_positions = []

    if isinstance(raw_positions, dict):
        raw_positions = raw_positions.get("positions", [])

    stock_prices = {}
    total_received = len(raw_positions)
    total_saved = 0
    total_dropped = 0

    for p in raw_positions:
        valid, reason = validate_position(p)
        ticker = p.get("ticker")
        if not valid:
            total_dropped += 1
            raw_val = {}
            # capture the raw problematic fields
            for k in ("currentPrice", "quantity", "averagePrice", "volume", "ppl"):
                if k in p:
                    raw_val[k] = p.get(k)
            logger.warning(f"Dropped position for {ticker or '<unknown>'}: {reason}; raw={json.dumps(raw_val, default=str)}")
            continue

        # coerce values
        avg_price = p.get("averagePrice", 0.0) or 0.0
        try:
            avg_price = float(avg_price)
        except Exception:
            avg_price = 0.0

        current_price = float(p.get("currentPrice"))
        quantity = float(p.get("quantity"))
        ppl = p.get("ppl", 0.0) or 0.0
        try:
            ppl = float(ppl)
        except Exception:
            ppl = 0.0

        value = quantity * current_price
        pos_pnl_pct = (ppl / (avg_price * quantity) * 100) if (avg_price and quantity) else 0.0
        volume = p.get("volume")

        conn.execute(
            "INSERT INTO positions (snapshot_id, ticker, quantity, avg_price, current_price, value, pnl, pnl_pct, volume) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (snapshot_id, ticker, quantity, avg_price, current_price, value, ppl, pos_pnl_pct, volume)
        )
        total_saved += 1
        if ticker and current_price:
            stock_prices[ticker] = current_price

    conn.commit()
    logger.info(f"Saved {total_saved} positions (received {total_received}, dropped {total_dropped})")

    # If all positions were dropped, warn and return early
    if total_saved == 0 and total_received > 0:
        logger.warning(f"All positions dropped during validation for snapshot {snapshot_id}; aborting further processing")
        _append_validation_log(ts, total_received, total_saved, total_dropped)
        conn.close()
        return snapshot_id, []

    # write validation log
    _append_validation_log(ts, total_received, total_saved, total_dropped)

    # Analyze and store recommendations
    try:
        recs = analyze_portfolio(account_info=account, stock_prices=stock_prices)
    except Exception as e:
        logger.error(f"Failed to analyze portfolio: {e}")
        recs = []

    for rec in recs:
        conn.execute(
            "INSERT INTO recommendations (snapshot_id, timestamp, ticker, action, reason, price) VALUES (?,?,?,?,?,?)",
            (snapshot_id, ts, rec.get("ticker"), rec.get("action"), rec.get("reason"), rec.get("current_price", 0.0))
        )
    conn.commit()
    logger.info(f"Saved {len(recs)} recommendations")

    conn.close()
    return snapshot_id, recs


if __name__ == "__main__":
    snapshot_id, recs = run_snapshot()
    print(f"Snapshot ID: {snapshot_id}, Recommendations: {len(recs)}")
