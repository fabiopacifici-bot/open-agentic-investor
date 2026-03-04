"""Tests for price_history DB integration and P&L SELL suppression."""
import sys
import os
import sqlite3
import tempfile
from datetime import date
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Helpers to create in-memory DB with price_history rows
# ---------------------------------------------------------------------------

PRICE_HISTORY_DDL = """
CREATE TABLE IF NOT EXISTS price_history (
    id      INTEGER PRIMARY KEY,
    ticker  TEXT    NOT NULL,
    date    TEXT    NOT NULL,
    close   REAL,
    volume  INTEGER,
    UNIQUE(ticker, date)
)
"""

POSITIONS_DDL = """
CREATE TABLE IF NOT EXISTS positions (
    id          INTEGER PRIMARY KEY,
    snapshot_id INTEGER,
    ticker      TEXT,
    pnl_pct     REAL
)
"""


def _make_db_with_prices(rows):
    """Return path to a temp DB pre-populated with price_history rows."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    conn.execute(PRICE_HISTORY_DDL)
    conn.executemany(
        "INSERT OR IGNORE INTO price_history (ticker, date, close, volume) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Test _fetch_price_history
# ---------------------------------------------------------------------------

def test_fetch_price_history_returns_closes():
    rows = [("AAPL", f"2025-01-{i:02d}", float(150 + i), 1000000) for i in range(1, 21)]
    db = _make_db_with_prices(rows)
    with patch("scripts.portfolio_manager.DB_PATH", db):
        from scripts.portfolio_manager import _fetch_price_history
        prices = _fetch_price_history("AAPL", limit=100)
    os.unlink(db)
    assert len(prices) == 20
    assert prices[0] == 151.0
    assert prices[-1] == 170.0


def test_fetch_price_history_empty_when_no_rows():
    db = _make_db_with_prices([])
    with patch("scripts.portfolio_manager.DB_PATH", db):
        from scripts.portfolio_manager import _fetch_price_history
        prices = _fetch_price_history("TSLA", limit=100)
    os.unlink(db)
    assert prices == []


# ---------------------------------------------------------------------------
# Test _fetch_volume_history
# ---------------------------------------------------------------------------

def test_fetch_volume_history_returns_volumes():
    rows = [("NVDA", f"2025-02-{i:02d}", 500.0, 2000000 + i * 1000) for i in range(1, 16)]
    db = _make_db_with_prices(rows)
    with patch("scripts.portfolio_manager.DB_PATH", db):
        from scripts.portfolio_manager import _fetch_volume_history
        vols = _fetch_volume_history("NVDA", limit=100)
    os.unlink(db)
    assert len(vols) == 15
    assert vols[0] == pytest_approx(2001000.0, rel=1e-6) if False else abs(vols[0] - 2001000.0) < 1


def test_fetch_volume_history_empty_when_no_rows():
    db = _make_db_with_prices([])
    with patch("scripts.portfolio_manager.DB_PATH", db):
        from scripts.portfolio_manager import _fetch_volume_history
        vols = _fetch_volume_history("MSFT", limit=100)
    os.unlink(db)
    assert vols == []


# ---------------------------------------------------------------------------
# Test P&L suppression
# ---------------------------------------------------------------------------

def test_sell_suppressed_when_pnl_below_minus5():
    """analyze_portfolio should NOT emit SELL when pnl_pct < -5."""
    from scripts.portfolio_manager import analyze_portfolio

    stock_prices = {"AAPL": 200.0}  # above sell threshold of 190

    config_mock = {
        "portfolio": [
            {"symbol": "AAPL", "buy_threshold": 100.0, "sell_threshold": 190.0}
        ]
    }

    with patch("scripts.portfolio_manager.load_portfolio_config", return_value=config_mock), \
         patch("scripts.portfolio_manager._build_indicator_reason", return_value=(None, "")), \
         patch("scripts.portfolio_manager._fetch_latest_pnl_pct", return_value=-10.0), \
         patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"):
        recs = analyze_portfolio(stock_prices=stock_prices)

    sell_recs = [r for r in recs if r["action"] == "SELL"]
    assert sell_recs == [], f"Expected no SELL, got {sell_recs}"


def test_sell_emitted_when_pnl_above_minus5():
    """analyze_portfolio SHOULD emit SELL when pnl_pct >= -5."""
    from scripts.portfolio_manager import analyze_portfolio

    stock_prices = {"AAPL": 200.0}
    config_mock = {
        "portfolio": [
            {"symbol": "AAPL", "buy_threshold": 100.0, "sell_threshold": 190.0}
        ]
    }

    with patch("scripts.portfolio_manager.load_portfolio_config", return_value=config_mock), \
         patch("scripts.portfolio_manager._build_indicator_reason", return_value=(None, "")), \
         patch("scripts.portfolio_manager._fetch_latest_pnl_pct", return_value=3.0), \
         patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"):
        recs = analyze_portfolio(stock_prices=stock_prices)

    sell_recs = [r for r in recs if r["action"] == "SELL"]
    assert len(sell_recs) == 1


def test_indicator_sell_suppressed_when_pnl_below_minus5():
    """Indicator-only SELL should also be suppressed when pnl_pct < -5."""
    from scripts.portfolio_manager import analyze_portfolio

    stock_prices = {"NVDA": 500.0}
    config_mock = {
        "portfolio": [
            {"symbol": "NVDA", "buy_threshold": None, "sell_threshold": None}
        ]
    }

    with patch("scripts.portfolio_manager.load_portfolio_config", return_value=config_mock), \
         patch("scripts.portfolio_manager._build_indicator_reason", return_value=("SELL", "RSI=75")), \
         patch("scripts.portfolio_manager._fetch_latest_pnl_pct", return_value=-15.0), \
         patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"):
        recs = analyze_portfolio(stock_prices=stock_prices)

    sell_recs = [r for r in recs if r["action"] == "SELL"]
    assert sell_recs == [], f"Expected no SELL, got {sell_recs}"


# ---------------------------------------------------------------------------
# Test cache-skip (no API call if today's rows exist)
# ---------------------------------------------------------------------------

def test_cache_skip_no_request_when_rows_exist():
    """fetch_daily_history should NOT call requests.get if today's row already in DB."""
    from scripts.fetch_daily_history import fetch_daily_history_for_tickers

    today = date.today().isoformat()
    rows = [("AAPL", today, 180.0, 5000000)]
    db = _make_db_with_prices(rows)

    with patch.dict(os.environ, {"ALPHA_API": "test_key", "INVESTMENTS_DB": db}), \
         patch("scripts.fetch_daily_history.requests.get") as mock_get:
        fetch_daily_history_for_tickers(["AAPL"], db_path=db)

    os.unlink(db)
    mock_get.assert_not_called()


def test_no_request_when_api_key_missing():
    """fetch_daily_history should silently skip when ALPHA_API is unset."""
    from scripts.fetch_daily_history import fetch_daily_history_for_tickers

    db = _make_db_with_prices([])
    env = {k: v for k, v in os.environ.items() if k != "ALPHA_API"}
    env["INVESTMENTS_DB"] = db

    with patch.dict(os.environ, env, clear=True), \
         patch("scripts.fetch_daily_history.requests.get") as mock_get:
        fetch_daily_history_for_tickers(["AAPL"], db_path=db)

    os.unlink(db)
    mock_get.assert_not_called()
