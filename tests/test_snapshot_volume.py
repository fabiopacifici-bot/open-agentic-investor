"""
test_snapshot_volume.py
Tests for volume column migration and snapshot insertion.
All tests use a temporary in-memory or temp-file SQLite DB — never touches the real DB.
"""

import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def make_db_with_positions(path: Path) -> sqlite3.Connection:
    """Create a minimal positions table without volume column."""
    conn = sqlite3.connect(path)
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
            FOREIGN KEY(snapshot_id) REFERENCES snapshots(id)
        );
    """)
    conn.commit()
    return conn


def column_names(conn: sqlite3.Connection, table: str) -> list:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


# ── migration tests ───────────────────────────────────────────────────────────

def test_migration_adds_volume_column():
    """Migration adds volume column to an existing DB without one."""
    from scripts.migrations.add_volume_column import run

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "portfolio.db"
        conn = make_db_with_positions(db_path)
        conn.close()

        run(db_path=db_path)

        conn = sqlite3.connect(db_path)
        cols = column_names(conn, "positions")
        conn.close()

        assert "volume" in cols


def test_migration_is_idempotent():
    """Running migration twice does not raise and is a no-op second time."""
    from scripts.migrations.add_volume_column import run

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "portfolio.db"
        conn = make_db_with_positions(db_path)
        conn.close()

        run(db_path=db_path)
        run(db_path=db_path)  # should not raise

        conn = sqlite3.connect(db_path)
        cols = column_names(conn, "positions")
        conn.close()

        assert cols.count("volume") == 1


def test_migration_creates_backup():
    """Migration writes a .db.bak file before altering."""
    from scripts.migrations.add_volume_column import run

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "portfolio.db"
        conn = make_db_with_positions(db_path)
        conn.close()

        run(db_path=db_path)

        bak_path = db_path.with_suffix(".db.bak")
        assert bak_path.exists(), "Backup .db.bak should be created"


def test_migration_skips_missing_db(capsys):
    """Migration does not crash when DB does not exist."""
    from scripts.migrations.add_volume_column import run

    db_path = Path("/tmp/nonexistent_test_portfolio_xyz.db")
    assert not db_path.exists()

    run(db_path=db_path)  # should not raise

    captured = capsys.readouterr()
    assert "skipping" in captured.out


# ── snapshot schema tests ─────────────────────────────────────────────────────

def test_snapshot_schema_has_volume_column():
    """init_db creates positions table with a volume column."""
    from scripts.snapshot import init_db

    conn = sqlite3.connect(":memory:")
    init_db(conn)
    cols = column_names(conn, "positions")
    conn.close()

    assert "volume" in cols


def test_snapshot_inserts_volume_when_present():
    """Snapshot INSERT stores volume when the API returns it."""
    from scripts.snapshot import init_db

    conn = sqlite3.connect(":memory:")
    init_db(conn)

    # Insert a fake snapshot row
    cur = conn.execute(
        "INSERT INTO snapshots (timestamp, total_value, cash, invested, pnl, pnl_pct) VALUES (?,?,?,?,?,?)",
        ("2026-01-01T00:00:00Z", 1000.0, 100.0, 900.0, 50.0, 5.0),
    )
    snapshot_id = cur.lastrowid

    # Simulate what snapshot.py does for a position with volume
    p = {
        "ticker": "AAPL",
        "quantity": 10.0,
        "averagePrice": 150.0,
        "currentPrice": 160.0,
        "ppl": 100.0,
        "volume": 5000000,
    }
    ticker = p.get("ticker")
    avg_price = p.get("averagePrice", 0.0) or 0.0
    current_price = p.get("currentPrice", 0.0) or 0.0
    quantity = p.get("quantity", 0.0) or 0.0
    ppl = p.get("ppl", 0.0) or 0.0
    value = quantity * current_price
    pos_pnl_pct = (ppl / (avg_price * quantity) * 100) if (avg_price and quantity) else 0.0
    volume = p.get("volume")

    conn.execute(
        "INSERT INTO positions (snapshot_id, ticker, quantity, avg_price, current_price, value, pnl, pnl_pct, volume) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (snapshot_id, ticker, quantity, avg_price, current_price, value, ppl, pos_pnl_pct, volume),
    )
    conn.commit()

    row = conn.execute("SELECT volume FROM positions WHERE ticker='AAPL'").fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 5000000


def test_snapshot_inserts_null_volume_when_absent():
    """Snapshot INSERT stores NULL when volume is not provided by the API."""
    from scripts.snapshot import init_db

    conn = sqlite3.connect(":memory:")
    init_db(conn)

    cur = conn.execute(
        "INSERT INTO snapshots (timestamp, total_value, cash, invested, pnl, pnl_pct) VALUES (?,?,?,?,?,?)",
        ("2026-01-01T00:00:00Z", 1000.0, 100.0, 900.0, 50.0, 5.0),
    )
    snapshot_id = cur.lastrowid

    p = {
        "ticker": "MSFT",
        "quantity": 5.0,
        "averagePrice": 300.0,
        "currentPrice": 310.0,
        "ppl": 50.0,
        # no 'volume' key
    }
    volume = p.get("volume")  # None

    conn.execute(
        "INSERT INTO positions (snapshot_id, ticker, quantity, avg_price, current_price, value, pnl, pnl_pct, volume) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (snapshot_id, p["ticker"], p["quantity"], p["averagePrice"], p["currentPrice"],
         p["quantity"] * p["currentPrice"], p["ppl"], 0.0, volume),
    )
    conn.commit()

    row = conn.execute("SELECT volume FROM positions WHERE ticker='MSFT'").fetchone()
    conn.close()

    assert row is not None
    assert row[0] is None
