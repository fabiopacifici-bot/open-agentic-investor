"""Stub: fetch_full_history
One-shot full history fetch using Alpha Vantage outputsize=full.
This is a safe stub: implements CLI, arg parsing, env read, and skips if alpha_sync.initial_synced is set.
Actual network calls should be implemented in follow-up.
"""

import os
import argparse
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get('INVEST_DB_PATH', os.path.join(os.path.expanduser('~'), 'Documents', 'Investments', 'portfolio.db'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tickers', help='Comma-separated list of tickers', default='')
    parser.add_argument('--tickers-file', help='File with one ticker per line')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    tickers = []
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',') if t.strip()]
    elif args.tickers_file:
        with open(args.tickers_file) as f:
            tickers = [ln.strip().upper() for ln in f if ln.strip()]
    else:
        print('No tickers specified. Exiting.')
        return

    api = os.environ.get('ALPHA_API')
    if not api:
        print('ALPHA_API not set in environment. Exiting.')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for ticker in tickers:
        cur.execute('SELECT initial_synced FROM alpha_sync WHERE ticker=?', (ticker,))
        row = cur.fetchone()
        if row and row[0]==1:
            print(f"{ticker}: already initial_synced. Skipping.")
            continue
        print(f"{ticker}: would fetch full history (stub).")
        if not args.dry_run:
            # mark initial_synced as done (stub behaviour)
            cur.execute('INSERT OR REPLACE INTO alpha_sync(ticker, initial_synced, last_success, failure_count) VALUES (?,?,?,?)',
                        (ticker, 1, datetime.utcnow().isoformat(), 0))
            conn.commit()
            print(f"{ticker}: marked initial_synced=1 (stub).")
    conn.close()


if __name__ == '__main__':
    main()
