"""
Tests for stop-loss automation — task #344.

All tests use either pure-function calls (signals.py) or in-memory / temp-file
SQLite DBs.  The live ~/Documents/Investments/portfolio.db is NEVER touched.
"""
import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Make sure repo root is on the path regardless of working directory
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.signals import check_trailing_stop_loss


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_with_price_history(ticker: str, prices: list[float]) -> str:
    """Create a temp SQLite DB with price_history and positions tables.

    Args:
        ticker: Ticker symbol.
        prices: List of closing prices (oldest first); dates assigned as
                2024-01-01, 2024-01-02, …

    Returns:
        Path to the temp DB file.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            date TEXT,
            close REAL,
            volume INTEGER
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
            volume INTEGER
        );
    """)
    for i, price in enumerate(prices):
        date = f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}"
        conn.execute(
            "INSERT INTO price_history (ticker, date, close, volume) VALUES (?,?,?,?)",
            (ticker, date, price, 1000),
        )
    conn.commit()
    conn.close()
    return tmp.name


def _add_position(db_path: str, ticker: str, avg_price: float):
    """Insert a positions row so _fetch_avg_price can find it."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO positions (snapshot_id, ticker, quantity, avg_price, current_price, value, pnl, pnl_pct) "
        "VALUES (1, ?, 10, ?, ?, 0, 0, 0)",
        (ticker, avg_price, avg_price),
    )
    conn.commit()
    conn.close()


MINIMAL_PORTFOLIO_CONFIG = {
    "portfolio": [
        {
            "symbol": "ORCL",
            "buy_threshold": 80.0,
            "sell_threshold": 120.0,
        }
    ]
}


# ---------------------------------------------------------------------------
# 1. check_trailing_stop_loss — pure-function unit tests
# ---------------------------------------------------------------------------


class TestCheckTrailingStopLoss:

    def test_neither_triggered(self):
        """No stop fires when current price is well above both thresholds."""
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=100.0,
            avg_price=90.0,
            thirty_day_high=105.0,
            trailing_pct=0.10,
            hard_stop_pct=0.15,
        )
        assert triggered is False
        assert reason == ""
        assert stop_type == "none"

    def test_trailing_stop_triggered(self):
        """Trailing stop fires when current < thirty_day_high * (1 - trailing_pct)."""
        # thirty_day_high = 100, trailing_pct = 0.10 → threshold = 90
        # current = 85 → 85 < 90 → trailing triggered
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=85.0,
            avg_price=80.0,      # avg * 0.85 = 68 → hard NOT triggered
            thirty_day_high=100.0,
            trailing_pct=0.10,
            hard_stop_pct=0.15,
        )
        assert triggered is True
        assert stop_type == "trailing"
        assert "Trailing stop" in reason
        assert "85.00" in reason
        assert "100.00" in reason
        assert "15.0" in reason  # 15% below high

    def test_hard_stop_triggered(self):
        """Hard stop fires when current < avg_price * (1 - hard_stop_pct)."""
        # avg = 100, hard_stop_pct = 0.15 → threshold = 85
        # current = 82 → 82 < 85 → hard triggered
        # thirty_day_high = 83 → trailing threshold = 83*0.9 = 74.7 → NOT triggered
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=82.0,
            avg_price=100.0,
            thirty_day_high=83.0,
            trailing_pct=0.10,
            hard_stop_pct=0.15,
        )
        assert triggered is True
        assert stop_type == "hard"
        assert "Hard stop" in reason
        assert "82.00" in reason
        assert "100.00" in reason

    def test_both_triggered_trailing_more_severe(self):
        """When both fire, return the one with the larger loss."""
        # trailing: 15% below high (high=100, current=85) → trailing triggered
        # hard: 12% below avg (avg=96.6, current=85) → hard triggered
        # trailing_drop = 15/100 = 0.15  >  hard_drop = 11.6/96.6 = 0.12 → trailing wins
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=85.0,
            avg_price=96.6,       # 85/96.6 = ~12% drop
            thirty_day_high=100.0,
            trailing_pct=0.10,    # threshold=90 → 85<90 triggered
            hard_stop_pct=0.10,   # threshold=86.94 → 85<86.94 triggered
        )
        assert triggered is True
        assert stop_type == "trailing"

    def test_both_triggered_hard_more_severe(self):
        """When both fire and hard is the bigger loss, return hard."""
        # avg=100, hard_stop_pct=0.15 → hard threshold=85, current=70 → hard_drop=30%
        # thirty_day_high=100, trailing_pct=0.10 → trailing threshold=90, current=70 → trailing_drop=30%
        # Equal: trailing drop = (100-70)/100 = 30%, hard_drop = (100-70)/100 = 30%
        # Both equal → trailing wins by >=
        # Let's make hard clearly bigger
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=70.0,
            avg_price=100.0,      # hard_drop = 30/100 = 30%
            thirty_day_high=95.0, # trailing_drop = 25/95 = 26.3%
            trailing_pct=0.10,    # threshold=85.5 → 70<85.5 triggered
            hard_stop_pct=0.15,   # threshold=85 → 70<85 triggered
        )
        assert triggered is True
        assert stop_type == "hard"
        assert "Hard stop" in reason

    def test_reason_format_trailing(self):
        """Reason string must contain expected percentage and price values."""
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=80.0,
            avg_price=90.0,
            thirty_day_high=100.0,
            trailing_pct=0.10,
            hard_stop_pct=0.15,
        )
        # 80 is 20% below 100-day high of 100
        assert triggered is True
        assert stop_type == "trailing"
        assert "20.0%" in reason

    def test_reason_format_hard(self):
        """Hard stop reason must mention avg price."""
        triggered, reason, stop_type = check_trailing_stop_loss(
            current_price=70.0,
            avg_price=100.0,
            thirty_day_high=68.0,   # 70 > 68*(1-0.10)=61.2 → trailing NOT triggered
            trailing_pct=0.10,
            hard_stop_pct=0.15,     # 70 < 100*0.85=85 → hard triggered
        )
        assert triggered is True
        assert stop_type == "hard"
        assert "30.0%" in reason
        assert "100.00" in reason


# ---------------------------------------------------------------------------
# 2. generate_recommendations (analyze_portfolio) with stop-loss mocked
# ---------------------------------------------------------------------------


class TestAnalyzePortfolioWithStopLoss:
    """Wire tests: verify stop-loss SELL is generated with reason prefix."""

    def _make_config_mock(self, ticker="ORCL", buy=80.0, sell=120.0):
        return {
            "portfolio": [
                {"symbol": ticker, "buy_threshold": buy, "sell_threshold": sell}
            ]
        }

    def test_stop_loss_sell_generated(self):
        """When trailing stop fires, SELL rec with STOP_LOSS prefix is returned."""
        from scripts.portfolio_manager import analyze_portfolio

        db_path = _make_db_with_price_history(
            "ORCL",
            prices=[100.0] * 30,  # 30-day high = 100
        )
        try:
            _add_position(db_path, "ORCL", avg_price=100.0)

            with (
                patch("scripts.portfolio_manager.load_portfolio_config",
                      return_value=self._make_config_mock("ORCL")),
                patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"),
                patch("scripts.portfolio_manager.DB_PATH", db_path),
                patch("scripts.portfolio_manager._fetch_thirty_day_high",
                      return_value=100.0),
                patch("scripts.portfolio_manager._fetch_avg_price",
                      return_value=100.0),
                patch("scripts.notifier.notify_channel"),
                patch.dict(os.environ, {"NO_OUTBOUND": "1"}),
            ):
                recs = analyze_portfolio(stock_prices={"ORCL": 85.0})  # 15% below high

            assert len(recs) == 1
            rec = recs[0]
            assert rec["ticker"] == "ORCL"
            assert rec["action"] == "SELL"
            assert rec["reason"].startswith("STOP_LOSS:")
            assert rec.get("stop_loss") is True
        finally:
            os.unlink(db_path)

    def test_stop_loss_sell_reason_prefix(self):
        """Reason must be prefixed with STOP_LOSS: and contain sl reason text."""
        from scripts.portfolio_manager import analyze_portfolio

        db_path = _make_db_with_price_history("BABA", prices=[120.0] * 30)
        try:
            _add_position(db_path, "BABA", avg_price=100.0)

            with (
                patch("scripts.portfolio_manager.load_portfolio_config",
                      return_value=self._make_config_mock("BABA", buy=70.0, sell=130.0)),
                patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"),
                patch("scripts.portfolio_manager.DB_PATH", db_path),
                patch("scripts.portfolio_manager._fetch_thirty_day_high",
                      return_value=120.0),
                patch("scripts.portfolio_manager._fetch_avg_price",
                      return_value=100.0),
                patch("scripts.notifier.notify_channel"),
                patch.dict(os.environ, {"NO_OUTBOUND": "1"}),
            ):
                recs = analyze_portfolio(stock_prices={"BABA": 78.0})
                # 78 < 120*0.90=108 → trailing triggered; 78 < 100*0.85=85 → hard triggered
                # hard_drop = 22%, trailing_drop = 35% → trailing wins

            assert len(recs) == 1
            rec = recs[0]
            assert rec["reason"].startswith("STOP_LOSS:")
            assert "stop" in rec["reason"].lower()
        finally:
            os.unlink(db_path)

    def test_no_stop_loss_when_above_thresholds(self):
        """No stop-loss rec when price is within bounds and no SL triggered."""
        from scripts.portfolio_manager import analyze_portfolio

        db_path = _make_db_with_price_history("MSFT", prices=[100.0] * 30)
        try:
            _add_position(db_path, "MSFT", avg_price=100.0)

            with (
                patch("scripts.portfolio_manager.load_portfolio_config",
                      return_value=self._make_config_mock("MSFT", buy=80.0, sell=120.0)),
                patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"),
                patch("scripts.portfolio_manager.DB_PATH", db_path),
                patch("scripts.portfolio_manager._fetch_thirty_day_high",
                      return_value=100.0),
                patch("scripts.portfolio_manager._fetch_avg_price",
                      return_value=100.0),
                patch("scripts.portfolio_manager._build_indicator_reason",
                      return_value=(None, "")),
                patch.dict(os.environ, {"NO_OUTBOUND": "1"}),
            ):
                # 95 is within 80-120 range AND above 90 trailing threshold
                recs = analyze_portfolio(stock_prices={"MSFT": 95.0})

            stop_loss_recs = [r for r in recs if r.get("stop_loss")]
            assert len(stop_loss_recs) == 0, f"Unexpected SL recs: {stop_loss_recs}"
        finally:
            os.unlink(db_path)

    def test_stop_loss_skips_threshold_logic(self):
        """When stop-loss fires, it should be the ONLY rec — threshold BUY/SELL skipped."""
        from scripts.portfolio_manager import analyze_portfolio

        db_path = _make_db_with_price_history("NVDA", prices=[100.0] * 30)
        try:
            _add_position(db_path, "NVDA", avg_price=100.0)

            with (
                patch("scripts.portfolio_manager.load_portfolio_config",
                      return_value=self._make_config_mock("NVDA", buy=90.0, sell=95.0)),
                patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"),
                patch("scripts.portfolio_manager.DB_PATH", db_path),
                patch("scripts.portfolio_manager._fetch_thirty_day_high",
                      return_value=100.0),
                patch("scripts.portfolio_manager._fetch_avg_price",
                      return_value=100.0),
                patch("scripts.notifier.notify_channel"),
                patch.dict(os.environ, {"NO_OUTBOUND": "1"}),
            ):
                # Price=85: below buy threshold (90) AND SL triggered (85<90 trailing).
                # Stop-loss should take precedence and generate SELL; BUY skipped.
                recs = analyze_portfolio(stock_prices={"NVDA": 85.0})

            assert len(recs) == 1
            assert recs[0]["action"] == "SELL"
            assert recs[0].get("stop_loss") is True
        finally:
            os.unlink(db_path)

    def test_stop_loss_telegram_alert_sent(self):
        """notify_channel must be called with STOP_LOSS message when triggered."""
        from scripts.portfolio_manager import analyze_portfolio

        db_path = _make_db_with_price_history("ORCL", prices=[100.0] * 30)
        try:
            _add_position(db_path, "ORCL", avg_price=100.0)

            mock_notify = MagicMock(return_value=True)

            with (
                patch("scripts.portfolio_manager.load_portfolio_config",
                      return_value=self._make_config_mock("ORCL")),
                patch("scripts.portfolio_manager.fetch_daily_history_for_tickers"),
                patch("scripts.portfolio_manager.DB_PATH", db_path),
                patch("scripts.portfolio_manager._fetch_thirty_day_high",
                      return_value=100.0),
                patch("scripts.portfolio_manager._fetch_avg_price",
                      return_value=100.0),
                patch("scripts.notifier.notify_channel", mock_notify),
                patch.dict(os.environ, {"NO_OUTBOUND": "1"}),
            ):
                analyze_portfolio(stock_prices={"ORCL": 85.0})

            # notify_channel should have been called at least once
            assert mock_notify.called
            call_args = mock_notify.call_args
            # First positional arg is the message
            msg = call_args[0][0] if call_args[0] else call_args[1].get("message", "")
            assert "STOP-LOSS" in msg or "🛑" in msg
            assert "ORCL" in msg
        finally:
            os.unlink(db_path)
