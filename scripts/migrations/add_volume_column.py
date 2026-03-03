"""
Migration: add_volume_column.py
Adds `volume` column (INTEGER, nullable) to the `positions` table.

Safe to run multiple times — no-op if column already exists.
Creates a backup of portfolio.db → portfolio.db.bak before altering.

Usage:
    python -m scripts.migrations.add_volume_column
"""

import shutil
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / "Documents" / "Investments" / "portfolio.db"
BAK_PATH = DB_PATH.with_suffix(".db.bak")


def run(db_path: Path = DB_PATH) -> None:
    if not db_path.exists():
        print(f"[add_volume_column] DB not found at {db_path}, skipping.")
        return

    # Backup before touching anything
    bak = db_path.with_suffix(".db.bak")
    shutil.copy2(db_path, bak)
    print(f"[add_volume_column] Backup written to {bak}")

    conn = sqlite3.connect(db_path)
    try:
        # Check whether column already exists (idempotent)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(positions)")]
        if "volume" in cols:
            print("[add_volume_column] Column 'volume' already exists — nothing to do.")
            return

        # Safe ALTER inside a transaction
        with conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("ALTER TABLE positions ADD COLUMN volume INTEGER")
            conn.execute("PRAGMA foreign_keys=ON")

        print("[add_volume_column] Column 'volume' added to positions table.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
