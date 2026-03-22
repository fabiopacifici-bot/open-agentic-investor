import sqlite3
import os
import tempfile
import json
from skills.open_agentic_investor.scripts import fetch_daily_incremental as fdi


def create_db_with_price_history(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS price_history (ticker TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, PRIMARY KEY(ticker,date))')
    cur.execute('CREATE TABLE IF NOT EXISTS alpha_sync (ticker TEXT PRIMARY KEY, initial_synced INTEGER DEFAULT 0, last_success TIMESTAMP, failure_count INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()


def test_pick_tickers_empty_alpha_sync():
    with tempfile.NamedTemporaryFile() as tf:
        db_path = tf.name
        create_db_with_price_history(db_path)
        conn = sqlite3.connect(db_path)
        # insert some price_history tickers
        cur = conn.cursor()
        cur.execute("INSERT INTO price_history(ticker,date,open,high,low,close,volume) VALUES ('AAPL','2020-01-01',1,1,1,1,100)")
        conn.commit()
        tickers = fdi.pick_tickers(conn, 5)
        assert 'AAPL' in tickers
        conn.close()


def test_process_response_inserts():
    with tempfile.NamedTemporaryFile() as tf:
        db_path = tf.name
        create_db_with_price_history(db_path)
        conn = sqlite3.connect(db_path)
        sample = {
            'Time Series (Daily)': {
                '2026-03-20': {'1. open':'100','2. high':'110','3. low':'90','4. close':'105','5. volume':'1000'}
            }
        }
        ok, inserted = fdi.process_response(conn, 'TEST', sample)
        assert ok
        assert inserted>=1
        conn.close()
