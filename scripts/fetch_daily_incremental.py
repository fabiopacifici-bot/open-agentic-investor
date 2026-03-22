"""Daily incremental fetcher for Alpha Vantage (basic implementation)
Features:
- Respects DAILY_TICKER_CAP
- Respects ALPHA_DELAY_SECONDS between requests
- Exponential backoff on 'Note' responses
- Updates alpha_sync table

This implementation uses requests to call Alpha Vantage and sqlite3 for DB operations.
"""

import os
import time
import sqlite3
import argparse
import requests
from datetime import datetime

DB_PATH = os.environ.get('INVEST_DB_PATH', os.path.join(os.path.expanduser('~'), 'Documents', 'Investments', 'portfolio.db'))
API_URL = 'https://www.alphavantage.co/query'

DAILY_TICKER_CAP = int(os.environ.get('DAILY_TICKER_CAP', '20'))
ALPHA_DELAY_SECONDS = float(os.environ.get('ALPHA_DELAY_SECONDS', '1.2'))
ALPHA_MAX_RETRIES = int(os.environ.get('ALPHA_MAX_RETRIES', '3'))
ALPHA_BACKOFF_BASE = float(os.environ.get('ALPHA_BACKOFF_BASE', '2'))


def pick_tickers(conn, cap):
    cur = conn.cursor()
    cur.execute("SELECT ticker FROM alpha_sync ORDER BY initial_synced ASC, last_success ASC NULLS FIRST LIMIT ?", (cap,))
    rows = cur.fetchall()
    if rows:
        return [r[0] for r in rows]
    # fallback: no alpha_sync entries; try to read tickers from price_history
    cur.execute('SELECT DISTINCT ticker FROM price_history LIMIT ?', (cap,))
    return [r[0] for r in cur.fetchall()]


def fetch_for_ticker(api_key, ticker):
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': ticker,
        'outputsize': 'compact',
        'apikey': api_key,
        'datatype': 'json'
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    return resp


def process_response(conn, ticker, resp_json):
    # resp_json expected to contain 'Time Series (Daily)'
    ts = resp_json.get('Time Series (Daily)')
    if not ts:
        return False, 'no_timeseries'
    cur = conn.cursor()
    inserted = 0
    for date_str, day in ts.items():
        # basic insert - assumes price_history has columns: ticker,date,open,high,low,close,volume
        try:
            cur.execute('INSERT OR IGNORE INTO price_history(ticker, date, open, high, low, close, volume) VALUES (?,?,?,?,?,?,?)',
                        (ticker, date_str, float(day['1. open']), float(day['2. high']), float(day['3. low']), float(day['4. close']), int(float(day['5. volume']))))
            if cur.rowcount>0:
                inserted += 1
        except Exception as e:
            # ignore row-level errors
            print(f"{ticker}: row insert error for {date_str}: {e}")
    conn.commit()
    return True, inserted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cap', type=int, help='override DAILY_TICKER_CAP')
    args = parser.parse_args()

    api_key = os.environ.get('ALPHA_API')
    if not api_key:
        print('ALPHA_API not set. Exiting.')
        return

    cap = args.cap or DAILY_TICKER_CAP

    conn = sqlite3.connect(DB_PATH)
    tickers = pick_tickers(conn, cap)
    print(f"Selected {len(tickers)} tickers to update")

    for ticker in tickers:
        # check today's row exists
        cur = conn.cursor()
        today = datetime.utcnow().date().isoformat()
        cur.execute('SELECT 1 FROM price_history WHERE ticker=? AND date=? LIMIT 1', (ticker, today))
        if cur.fetchone():
            print(f"{ticker}: today's row exists. Skipping.")
            continue

        retries = 0
        while retries <= ALPHA_MAX_RETRIES:
            resp = None
            try:
                resp = fetch_for_ticker(api_key, ticker)
            except Exception as e:
                print(f"{ticker}: request error: {e}")
                resp = None

            if resp is None:
                retries += 1
                sleep = ALPHA_BACKOFF_BASE * (2 ** (retries-1))
                print(f"{ticker}: sleeping {sleep}s before retry (network)")
                time.sleep(sleep)
                continue

            if resp.status_code != 200:
                print(f"{ticker}: HTTP {resp.status_code}. Response: {resp.text[:200]}")
                retries += 1
                sleep = ALPHA_BACKOFF_BASE * (2 ** (retries-1))
                time.sleep(sleep)
                continue

            j = resp.json()
            # detect rate limit note
            if 'Note' in j or 'Information' in j:
                retries += 1
                sleep = ALPHA_BACKOFF_BASE * (2 ** (retries-1))
                print(f"{ticker}: rate-limited by Alpha Vantage. Backing off {sleep}s (retry {retries})")
                time.sleep(sleep)
                continue

            ok, result = process_response(conn, ticker, j)
            now_iso = datetime.utcnow().isoformat()
            if ok:
                # update alpha_sync
                cur.execute('INSERT OR REPLACE INTO alpha_sync(ticker, initial_synced, last_success, failure_count) VALUES (?,?,?,?)',
                            (ticker, 1, now_iso, 0))
                conn.commit()
                print(f"{ticker}: success. inserted={result}")
            else:
                # mark failure
                cur.execute('INSERT OR REPLACE INTO alpha_sync(ticker, initial_synced, last_success, failure_count) VALUES (?,?,?,?)',
                            (ticker, 0, None,  sqlite3.Binary(b'0')))
                conn.commit()
                print(f"{ticker}: failed to process response: {result}")
            break

        # delay between requests
        time.sleep(ALPHA_DELAY_SECONDS)

    conn.close()

if __name__ == '__main__':
    main()
