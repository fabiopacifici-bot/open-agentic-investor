"""
weekly_recalibrate.py — Weekly threshold sanity check and recalibration.

Usage:
    python -m scripts.weekly_recalibrate           # dry-run (print only)
    python -m scripts.weekly_recalibrate --apply   # write corrected thresholds to config.json
    python -m scripts.weekly_recalibrate --dry-run # explicit dry-run
"""

import argparse
import os
import sqlite3
from credential_handler import load_environment
from scripts.portfolio_manager import load_portfolio_config, save_portfolio_config
from utils.logger import logger

DB_PATH = os.environ.get("INVESTMENTS_DB", os.path.expanduser("~/Documents/Investments/portfolio.db"))


def get_latest_positions():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT ticker, avg_price, current_price, quantity
        FROM positions
        WHERE snapshot_id = (SELECT MAX(id) FROM snapshots)
    """).fetchall()
    conn.close()
    return [{"ticker": r[0], "avg_price": r[1], "current_price": r[2], "quantity": r[3]} for r in rows]


def recalibrate(apply=False):
    load_environment()
    positions = get_latest_positions()
    config = load_portfolio_config()
    portfolio_map = {item['symbol']: item for item in config.get('portfolio', [])}

    issues = []
    fixes = []

    for pos in positions:
        ticker = pos['ticker']
        avg = pos['avg_price'] or 0
        price = pos['current_price'] or 0
        cfg = portfolio_map.get(ticker)

        if not cfg or not avg or not price:
            continue

        if cfg.get('manual'):
            print(f"  ⏭  {ticker}: manual override — skipping")
            continue

        sell = cfg.get('sell_threshold', 0)
        buy = cfg.get('buy_threshold', 0)
        ideal_sell = round(avg * 1.20, 2)
        ideal_buy = round(avg * 0.90, 2)

        flagged = False

        # Flag: sell threshold below current price (would fire immediately)
        if sell and sell < price:
            issues.append(f"  ⚠️  {ticker}: sell threshold ${sell} is BELOW current price ${price:.2f} — stale!")
            cfg['sell_threshold'] = round(price * 1.15, 2)
            fixes.append(f"  ✅ {ticker}: sell → ${cfg['sell_threshold']} (current price + 15%)")
            flagged = True

        # Flag: buy threshold too close to current price (would fire as noise)
        if buy and buy > price * 0.95:
            issues.append(f"  ⚠️  {ticker}: buy threshold ${buy} is within 5% of current price ${price:.2f} — too tight!")
            cfg['buy_threshold'] = round(price * 0.88, 2)
            fixes.append(f"  ✅ {ticker}: buy → ${cfg['buy_threshold']} (current price - 12%)")
            flagged = True

        # Flag: sell threshold never been updated from a stale value
        if sell and sell < ideal_sell * 0.80:
            issues.append(f"  ⚠️  {ticker}: sell ${sell} is well below ideal ${ideal_sell} (avg*1.2) — outdated config")
            if not flagged:
                cfg['sell_threshold'] = ideal_sell
                fixes.append(f"  ✅ {ticker}: sell → ${ideal_sell} (avg_price * 1.20)")

    print("\n📋 Weekly Recalibration Report")
    print("=" * 40)

    if not issues:
        print("✅ All thresholds look healthy — no issues found.")
    else:
        print(f"\n🔍 Found {len(issues)} issue(s):\n")
        for i in issues:
            print(i)
        print(f"\n🔧 Proposed fixes ({len(fixes)}):\n")
        for f in fixes:
            print(f)

        if apply:
            save_portfolio_config(config)
            print("\n✅ Config updated and saved.")
        else:
            print("\n⚡ Run with --apply to write these fixes to config.json")

    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly threshold recalibration")
    parser.add_argument('--apply', action='store_true', help='Apply fixes to config.json')
    parser.add_argument('--dry-run', action='store_true', help='Print only, no writes (default)')
    args = parser.parse_args()
    recalibrate(apply=args.apply)
