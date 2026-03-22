"""
Migration: add_price_history_table.py
Creates the `price_history` table for storing daily OHLCV data from Alpha Vantage.

Schema:
    price_history (id INTEGER PRIMARY KEY, ticker TEXT, date TEXT, close REAL,
                   volume INTEGER, UNIQUE(ticker, date))

Safe to run multiple times — idempotent (CREATE TABLE IF NOT EXISTS).
Creates a backup of portfolio.db → portfolio.db.bak before altering.

Usage:
    python -m scripts.migrations.add_price_history_table
"""

import shutil
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "Documents" / "Investments" / "portfolio.db"


def run(db_path: Path = DB_PATH) -> None:
    if not db_path.exists():
        print(f"[add_price_history_table] DB not found at {db_path}, skipping.")
        return

    # Backup before touching anything
    bak = db_path.with_suffix(".db.bak")
    shutil.copy2(db_path, bak)
    print(f"[add_price_history_table] Backup written to {bak}")

    conn = sqlite3.connect(db_path)
    try:
        with conn:
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
        print("[add_price_history_table] Table 'price_history' is ready.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
