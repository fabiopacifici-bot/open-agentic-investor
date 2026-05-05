"""Regression tests for auto_calibrate_thresholds.

Covers issue #15: OperationalError crash when avg_price_history / price_highs
tables are absent from a fresh database.
"""

import os
import sqlite3
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.portfolio_manager import auto_calibrate_thresholds

EMPTY_CONFIG = {"portfolio": []}

POSITIONS = [
    {"ticker": "AAPL", "avg_price": 150.00, "current_price": 160.00},
]


def _make_empty_db() -> str:
    """Return path to a temp SQLite DB that has NO calibration tables."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAutoCalibrateFreshDB:
    """auto_calibrate_thresholds must not crash on a fresh DB."""

    def test_no_operationalerror_on_missing_tables(self):
        """Issue #15: should NOT raise OperationalError when tables are absent."""
        db_path = _make_empty_db()
        try:
            with (
                patch(
                    "scripts.portfolio_manager.load_portfolio_config",
                    return_value=EMPTY_CONFIG.copy(),
                ),
                patch("scripts.portfolio_manager.save_portfolio_config"),
            ):
                # Must complete without raising sqlite3.OperationalError
                auto_calibrate_thresholds(POSITIONS, db_path=db_path)
        finally:
            os.unlink(db_path)

    def test_tables_created_after_first_run(self):
        """Tables avg_price_history and price_highs should exist after first call."""
        db_path = _make_empty_db()
        try:
            with (
                patch(
                    "scripts.portfolio_manager.load_portfolio_config",
                    return_value=EMPTY_CONFIG.copy(),
                ),
                patch("scripts.portfolio_manager.save_portfolio_config"),
            ):
                auto_calibrate_thresholds(POSITIONS, db_path=db_path)

            conn = sqlite3.connect(db_path)
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            conn.close()
            assert "avg_price_history" in tables
            assert "price_highs" in tables
        finally:
            os.unlink(db_path)

    def test_thresholds_written_correctly(self):
        """buy/sell thresholds are derived from avg_price on first run."""
        db_path = _make_empty_db()
        captured_config = {}

        def fake_save(cfg):
            captured_config.update(cfg)

        try:
            with (
                patch(
                    "scripts.portfolio_manager.load_portfolio_config",
                    return_value=EMPTY_CONFIG.copy(),
                ),
                patch(
                    "scripts.portfolio_manager.save_portfolio_config",
                    side_effect=fake_save,
                ),
            ):
                auto_calibrate_thresholds(POSITIONS, db_path=db_path)
        finally:
            os.unlink(db_path)

        entry = next(
            (e for e in captured_config.get("portfolio", []) if e["symbol"] == "AAPL"),
            None,
        )
        assert entry is not None, "AAPL should be present in saved config"
        assert entry["buy_threshold"] == round(150.00 * 0.90, 2)
        # sell = max(avg*1.20, peak*0.85); peak=current_price=160
        expected_sell = max(round(150.00 * 1.20, 2), round(160.00 * 0.85, 2))
        assert entry["sell_threshold"] == expected_sell

    def test_idempotent_on_repeated_calls(self):
        """Calling twice with same prices should not crash or duplicate rows."""
        db_path = _make_empty_db()
        try:
            with (
                patch(
                    "scripts.portfolio_manager.load_portfolio_config",
                    return_value=EMPTY_CONFIG.copy(),
                ),
                patch("scripts.portfolio_manager.save_portfolio_config"),
            ):
                auto_calibrate_thresholds(POSITIONS, db_path=db_path)

            with (
                patch(
                    "scripts.portfolio_manager.load_portfolio_config",
                    return_value=EMPTY_CONFIG.copy(),
                ),
                patch("scripts.portfolio_manager.save_portfolio_config"),
            ):
                auto_calibrate_thresholds(POSITIONS, db_path=db_path)

            conn = sqlite3.connect(db_path)
            count = conn.execute(
                "SELECT COUNT(*) FROM avg_price_history WHERE ticker='AAPL'"
            ).fetchone()[0]
            conn.close()
            assert count == 1, (
                "INSERT OR REPLACE should keep exactly one row per ticker"
            )
        finally:
            os.unlink(db_path)
