#!/usr/bin/env python3
"""
investor_monitor.py — Dedicated portfolio monitor sub-agent.

Runs on a loop, takes snapshots every 15 minutes (or every 5 min during market hours),
sends Telegram alerts for:
  - BUY/SELL signals (threshold breaches)
  - P&L change >3% vs last snapshot
  - Any position move >5% intraday
  - Periodic summary every 30 minutes during market hours

Run: python3 scripts/investor_monitor.py
"""

import os
import sys
import time
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Run from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# chdir to repo root so credential_handler finds .env
os.chdir(str(REPO_ROOT))

from credential_handler import load_environment as load_credentials
load_credentials()

from scripts.snapshot import run_snapshot
from scripts.report_export import run_export
from utils.logger import logger

TELEGRAM_CHAT_ID = "6395145098"

def notify_channel(text: str):
    """Send message via OpenClaw CLI (Telegram)."""
    import subprocess
    result = subprocess.run(
        ["openclaw", "message", "send",
         "--channel", "telegram",
         "--target", TELEGRAM_CHAT_ID,
         "-m", text],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"notify_channel failed: {result.stderr}")
    else:
        logger.info("Telegram message sent")

def send_report_file(filepath: str, caption: str = "📊 Portfolio Report"):
    """Send HTML report via OpenClaw CLI."""
    import subprocess
    result = subprocess.run(
        ["openclaw", "message", "send",
         "--channel", "telegram",
         "--target", TELEGRAM_CHAT_ID,
         "--media", filepath,
         "-m", caption],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"send_report_file failed: {result.stderr}")
    else:
        logger.info(f"Report file sent: {filepath}")

DB_PATH = Path(os.path.expanduser("~/Documents/Investments/portfolio.db"))
BERLIN = ZoneInfo("Europe/Berlin")

# Config
ALERT_ON_DB_RECS = True  # If True, fall back to DB-stored recommendations when analyzer returned none

MARKET_OPEN_H, MARKET_OPEN_M = 15, 30   # 15:30 Berlin
MARKET_CLOSE_H, MARKET_CLOSE_M = 22, 0  # 22:00 Berlin

SNAPSHOT_INTERVAL_MARKET = 15 * 60   # 15 min during market hours
SNAPSHOT_INTERVAL_OFF    = 30 * 60   # 30 min outside market hours
SUMMARY_INTERVAL         = 30 * 60   # full summary every 30 min
PNL_CHANGE_THRESHOLD     = 3.0       # % portfolio P&L change alert
POSITION_MOVE_THRESHOLD  = 5.0       # % single position move alert

last_pnl = None
last_positions = {}
last_summary_time = 0

# In-memory sent-alerts tracking to avoid duplicates
# Structure: { snapshot_id: set( "TICKER|ACTION" ) }
sent_alerts_store: dict[int, set[str]] = {}


def is_market_open() -> bool:
    now = datetime.now(BERLIN)
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    open_min  = MARKET_OPEN_H  * 60 + MARKET_OPEN_M
    close_min = MARKET_CLOSE_H * 60 + MARKET_CLOSE_M
    current   = now.hour * 60 + now.minute
    return open_min <= current < close_min


def get_latest_snapshot():
    if not DB_PATH.exists():
        return None, []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    snap = conn.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
    positions = []
    if snap:
        positions = conn.execute(
            "SELECT ticker, current_price, pnl, pnl_pct FROM positions WHERE snapshot_id=?",
            (snap["id"],)
        ).fetchall()
    conn.close()
    return snap, positions


def format_summary(snap, positions) -> str:
    ts = datetime.fromisoformat(snap["timestamp"]).astimezone(BERLIN).strftime("%H:%M CET")
    lines = [
        f"📊 *Portfolio Update — {ts}*",
        f"💰 Total: €{snap['total_value']:.2f} | P&L: €{snap['pnl']:.2f} ({snap['pnl_pct']:.2f}%)",
        f"💵 Cash: €{snap['cash']:.2f} | Invested: €{snap['invested']:.2f}",
        "",
        "📈 *Positions:*"
    ]
    sorted_pos = sorted(positions, key=lambda r: r["pnl_pct"], reverse=True)
    for p in sorted_pos:
        icon = "🟢" if p["pnl_pct"] >= 0 else "🔴"
        ticker = p["ticker"].replace("_US_EQ", "")
        lines.append(f"  {icon} {ticker}: €{p['current_price']:.2f} | {p['pnl_pct']:.2f}% (€{p['pnl']:.2f})")
    return "\n".join(lines)


def check_alerts(snap, positions, recs) -> list[tuple[str, str|None]]:
    """Return list of tuples: (alert_text, dedup_key_or_None).
    dedup_key is in the form TICKER|ACTION for BUY/SELL signals, None for other alerts.
    """
    global last_pnl, last_positions
    alerts: list[tuple[str, str|None]] = []

    # 1. BUY/SELL signals
    for rec in recs:
        action = rec.get("action")
        ticker_raw = rec.get("ticker", "")
        ticker = ticker_raw.replace("_US_EQ", "")
        price  = rec.get("current_price", 0)
        reason = rec.get("reason", "")
        icon   = "🟢" if action == "BUY" else "🔴"
        text = f"{icon} *{action} Signal: {ticker}* @ €{price:.2f}\n_{reason}_"
        dedup_key = f"{ticker}|{action}" if ticker and action else None
        alerts.append((text, dedup_key))

    # 2. Portfolio P&L change
    if last_pnl is not None and snap:
        change = snap["pnl_pct"] - last_pnl
        if abs(change) >= PNL_CHANGE_THRESHOLD:
            direction = "📈" if change > 0 else "📉"
            alerts.append((
                f"{direction} *Portfolio moved {change:+.2f}%* since last check\n"
                f"Now: {snap['pnl_pct']:.2f}% | P&L: €{snap['pnl']:.2f}",
                None
            ))

    # 3. Individual position moves
    for p in positions:
        ticker = p["ticker"]
        prev = last_positions.get(ticker)
        if prev is not None:
            move = p["pnl_pct"] - prev
            if abs(move) >= POSITION_MOVE_THRESHOLD:
                short = ticker.replace("_US_EQ", "")
                direction = "📈" if move > 0 else "📉"
                alerts.append((
                    f"{direction} *{short} moved {move:+.2f}%* since last check → now {p['pnl_pct']:.2f}%",
                    None
                ))

    # Update state
    if snap:
        last_pnl = snap["pnl_pct"]
    last_positions = {p["ticker"]: p["pnl_pct"] for p in positions}

    return alerts


def run_cycle():
    global last_summary_time
    logger.info("Running snapshot...")
    try:
        snapshot_id, recs = run_snapshot()
    except Exception as e:
        notify_channel(f"⚠️ *Investor Monitor Error*\nSnapshot failed: {e}")
        logger.error(f"Snapshot error: {e}")
        return

    snap, positions = get_latest_snapshot()
    if snap is None:
        logger.warning("No snapshot data found after run")
        return

    # Prefer recommendations recorded in DB for this snapshot (robustness)
    analyzer_recs = recs if recs is not None else []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        db_recs = conn.execute(
            "SELECT ticker AS ticker, action AS action, reason AS reason, price AS current_price FROM recommendations WHERE snapshot_id = ?",
            (snap["id"],)
        ).fetchall()
        conn.close()
        db_recs = [dict(r) for r in db_recs] if db_recs else []
    except Exception as e:
        logger.warning(f"Failed to load recommendations from DB: {e}")
        db_recs = []

    # If analyzer returned no recs, optionally fall back to DB-backed recs
    if (not analyzer_recs) and db_recs and ALERT_ON_DB_RECS:
        recs = db_recs
        logger.info(f"Using DB-backed recs for snapshot {snap['id']} — analyzer returned 0")
    else:
        recs = analyzer_recs

    # Build alerts (with dedup keys)
    alerts = check_alerts(snap, positions, recs)

    # Prune sent_alerts_store to keep only the last 10 snapshot ids
    try:
        keep = 10
        keys_sorted = sorted(sent_alerts_store.keys())
        if len(keys_sorted) > keep:
            for k in keys_sorted[:-keep]:
                sent_alerts_store.pop(k, None)
    except Exception:
        # Non-fatal pruning errors shouldn't stop alerts
        pass

    # Send alerts, skipping duplicates for BUY/SELL signals
    for text, dedup_key in alerts:
        skip = False
        if dedup_key and snap and isinstance(snap.get("id"), int):
            s_id = snap["id"]
            sent_set = sent_alerts_store.setdefault(s_id, set())
            if dedup_key in sent_set:
                skip = True
            else:
                sent_set.add(dedup_key)
        if skip:
            logger.info(f"Skipping duplicate alert for {dedup_key} (snapshot {snap.get('id')})")
            continue
        notify_channel(text)
        logger.info(f"Alert sent: {text[:60]}")

    # Periodic full summary during market hours
    now = time.time()
    if is_market_open() and (now - last_summary_time >= SUMMARY_INTERVAL):
        summary = format_summary(snap, positions)
        notify_channel(summary)
        last_summary_time = now
        logger.info("Summary sent")

        # Also send full HTML report every hour (when market open)
        try:
            report_path = run_export()
            if report_path:
                send_report_file(str(report_path), caption="📊 Investor Report")
        except Exception as e:
            logger.warning(f"Report export failed: {e}")


def main():
    logger.info("🚀 Investor monitor started")
    notify_channel("🚀 *Investor Monitor Online*\nTracking your portfolio — alerts active.")

    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"Cycle error: {e}")

        interval = SNAPSHOT_INTERVAL_MARKET if is_market_open() else SNAPSHOT_INTERVAL_OFF
        status = "market hours" if is_market_open() else "off-hours"
        logger.info(f"Next check in {interval//60}m ({status})")
        time.sleep(interval)


if __name__ == "__main__":
    main()
