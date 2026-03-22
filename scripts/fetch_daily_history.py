"""
fetch_daily_history.py
Fetches TIME_SERIES_DAILY data from Alpha Vantage for a list of tickers and
caches the results in the price_history table.

Usage (standalone):
    python -m scripts.fetch_daily_history

Called from portfolio_manager.analyze_portfolio() before the ticker loop.
"""

import os
import re
import sqlite3
import logging
from datetime import date

import requests

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get(
    "INVESTMENTS_DB", os.path.expanduser("~/Documents/Investments/portfolio.db")
)
AV_BASE = "https://www.alphavantage.co/query"
FREE_TIER_CAP = 25


def _clean_ticker(raw: str) -> str:
    """Strip exchange suffixes like _US_EQ, _LSE_EQ, etc.

    Examples:
        NVDA_US_EQ  -> NVDA
        AAPL_US_EQ  -> AAPL
        BP_LSE_EQ   -> BP
        TSLA        -> TSLA  (unchanged)
    """
    return re.sub(r"_[A-Z]+_[A-Z]+$", "", raw)


def _today_row_exists(conn: sqlite3.Connection, ticker: str) -> bool:
    """Return True if a row for *ticker* dated today already exists."""
    today = date.today().isoformat()
    cur = conn.execute(
        "SELECT 1 FROM price_history WHERE ticker=? AND date=? LIMIT 1",
        (ticker, today),
    )
    return cur.fetchone() is not None


def fetch_daily_history_for_tickers(
    tickers: list, db_path: str = DB_PATH
) -> None:
    """Fetch and cache daily close/volume for every ticker in *tickers*.

    - Skips tickers whose today-row already exists (cache).
    - Uses Alpha Vantage TIME_SERIES_DAILY with outputsize=compact (100 days).
    - Reads ALPHA_API from env.
    - One failure per ticker does NOT abort the others.
    """
    api_key = os.environ.get("ALPHA_API")
    if not api_key:
        logger.warning("ALPHA_API env var not set — skipping daily history fetch.")
        return

    if not os.path.exists(db_path):
        logger.warning(f"DB not found at {db_path} — skipping daily history fetch.")
        return

    if len(tickers) > FREE_TIER_CAP:
        logger.warning(
            f"fetch_daily_history: {len(tickers)} tickers requested but free tier "
            f"cap is {FREE_TIER_CAP}/min — proceeding anyway, may get rate-limited."
        )

    conn = sqlite3.connect(db_path)
    try:
        # Ensure table exists (idempotent)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id      INTEGER PRIMARY KEY,
                ticker  TEXT    NOT NULL,
                date    TEXT    NOT NULL,
                close   REAL,
                volume  INTEGER,
                UNIQUE(ticker, date)
            )
            """
        )
        conn.commit()

        for raw_ticker in tickers:
            av_ticker = _clean_ticker(raw_ticker)
            try:
                if _today_row_exists(conn, raw_ticker):
                    logger.debug(f"[fetch_daily_history] Cache hit for {raw_ticker} — skipping.")
                    continue

                logger.info(f"[fetch_daily_history] Fetching {av_ticker} from Alpha Vantage…")
                resp = requests.get(
                    AV_BASE,
                    params={
                        "function": "TIME_SERIES_DAILY",
                        "symbol": av_ticker,
                        "outputsize": "compact",
                        "apikey": api_key,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

                time_series = data.get("Time Series (Daily)")
                if not time_series:
                    note = data.get("Note") or data.get("Information") or "unknown"
                    logger.warning(
                        f"[fetch_daily_history] No time series for {av_ticker}: {note}"
                    )
                    continue

                rows = []
                for day, vals in time_series.items():
                    try:
                        close = float(vals["4. close"])
                        volume = int(vals["5. volume"])
                        rows.append((raw_ticker, day, close, volume))
                    except (KeyError, ValueError) as e:
                        logger.debug(f"[fetch_daily_history] Skipping row {day}: {e}")

                conn.executemany(
                    "INSERT OR IGNORE INTO price_history (ticker, date, close, volume) "
                    "VALUES (?, ?, ?, ?)",
                    rows,
                )
                conn.commit()
                logger.info(
                    f"[fetch_daily_history] Inserted {len(rows)} rows for {raw_ticker}."
                )

            except Exception as e:
                logger.error(
                    f"[fetch_daily_history] Failed for {raw_ticker}: {e}", exc_info=True
                )
    finally:
        conn.close()
