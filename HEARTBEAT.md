# HEARTBEAT.md

## Periodic Monitoring

- **Task:** Monitor stock prices and notifications for urgent updates.
- **Frequency:** Every 30 minutes.
- **Actions:**
  1. Fetch stock prices.
  2. Check if any stock prices break defined thresholds.
  3. Send notifications for actionable items.

## 15-Minute Snapshot Heartbeat

- **Frequency:** Every 15 minutes.
- **Actions:**
  1. Run `python -m scripts.snapshot` from repo root — fetches live portfolio data, stores to `~/Documents/Investments/portfolio.db`.
  2. Check `recommendations` table for any new `BUY` or `SELL` signals.
  3. If BUY/SELL signals found: send Telegram alert with ticker, action, price, reason.
  4. Always include portfolio P&L summary in the alert.

### BUY/SELL Alert Logic
```python
from scripts.snapshot import run_snapshot
snapshot_id, recs = run_snapshot()
signals = [r for r in recs if r.get('action') in ('BUY', 'SELL')]
if signals:
    # send Telegram notification
```

### Running the Heartbeat Manually
```bash
cd /path/to/open-agentic-investor
python -m scripts.snapshot
```
