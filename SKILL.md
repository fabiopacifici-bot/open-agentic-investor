---
name: open-agentic-investor
description: Comprehensive portfolio management, stock analysis, and notification skill for Trading212 users.
metadata:
  version: 1.1.0
---

# Open-Agentic-Investor Skill

## 🚀 `/investor` — Main Entry Point

**Triggers:** `/investor`, `/portfolio`, `/open_agentic_investor`

When any of these commands arrive, immediately:

1. Run a live snapshot:
   ```bash
   cd /home/pacificDev/.openclaw/workspace/repositories/open-agentic-investor
   python -m scripts.snapshot
   ```

2. Pull the latest data from SQLite and format a summary (see **Live Summary Format** below).

3. Send the summary + inline buttons via the `message` tool:

```
📊 *Portfolio — <HH:MM CET>*
💰 Total: €X,XXX.XX | P&L: €±XXX (±X.XX%)
💵 Cash: €XXX | Invested: €X,XXX

_Tap a button below:_
```

**Buttons (2 rows):**
```json
[
  [
    {"text": "📊 Full Report",    "callback_data": "investor_report"},
    {"text": "⚡ Live Summary",   "callback_data": "investor_live"}
  ],
  [
    {"text": "🔔 15m Alerts",     "callback_data": "investor_freq_15"},
    {"text": "🔕 Pause Alerts",   "callback_data": "investor_freq_off"}
  ],
  [
    {"text": "📈 Top Movers",     "callback_data": "investor_movers"},
    {"text": "🚦 BUY/SELL Signals","callback_data": "investor_signals"}
  ]
]
```

### Callback Handlers

| `callback_data`      | Action |
|----------------------|--------|
| `investor_report`    | Snapshot → export HTML → `send_report_file()` to Telegram |
| `investor_live`      | Snapshot → send full text summary (all positions, P&L, signals) |
| `investor_movers`    | Sort positions by `pnl_pct`, show top 3 gainers + top 3 losers |
| `investor_signals`   | Show all BUY/SELL recommendations from latest snapshot |
| `investor_freq_15`   | Reply: "✅ Alerts every 15 minutes" |
| `investor_freq_off`  | Reply: "🔕 Alerts paused" |

---

### Live Summary Format

```
📊 *Portfolio Summary — 17:00 CET*
💰 Total: €3,380 | P&L: -€767 (-19.27%)
💵 Cash: €5 | Invested: €3,981

📈 *Top movers:*
  🟢 EBAY +0.34% | 🔴 SOUN -16.35% | 🔴 TEAM -18.23%

🚦 *Signals:* 2 BUY · 0 SELL
```

---

## Overview
Full Trading212 portfolio management: live snapshots, P&L tracking, BUY/SELL signals, HTML reports, and Telegram alerts.

**Repo:** `repositories/open-agentic-investor`
**DB:** `~/Documents/Investments/portfolio.db`
**Monitor:** `scripts/investor_monitor.py` (background, PID tracked in logs)

## Prerequisites
- Python 3.8+ with venv activated
- `.env` in repo root with `API_KEY`, `API_BASE_URL`
- OpenClaw CLI for Telegram delivery (no separate bot token needed)

## Dashboard & Reports

### Data Directory
All data files (SQLite, HTML exports) are stored at `~/Documents/Investments/` — **never in the repo**.

### Snapshot Only
```bash
cd repositories/open-agentic-investor
python -m scripts.snapshot
```

### Export HTML Report
```bash
python -m scripts.report_export
```

### Start Web Dashboard
```bash
python -m dashboard.app
# Open http://localhost:5001
```

### SQLite Schema
- `snapshots` — timestamp, total_value, cash, invested, pnl, pnl_pct
- `positions` — ticker, quantity, current_price, market_value, pnl, pnl_pct
- `recommendations` — ticker, action, reason, current_price

## Background Monitor

The `investor_monitor.py` script runs continuously:
- **Off-hours:** checks every 30 min
- **Market hours (15:30–22:00 CET):** checks every 15 min
- Alerts fire on: BUY/SELL signals, ±3% portfolio move, ±5% position move
- Full summary sent every 30 min during market hours

**Start monitor:**
```bash
cd repositories/open-agentic-investor
python scripts/investor_monitor.py >> logs/monitor.log 2>&1 &
```

**Check if running:**
```bash
pgrep -fa investor_monitor
tail -20 repositories/open-agentic-investor/logs/monitor.log
```

## 🔍 Sub-Agent Health Check

To ensure all sub-agents are working properly during your exam period:

### Monitor Status
```bash
# Check if investor monitor is running
pgrep -fa investor_monitor

# Check recent snapshots
sqlite3 ~/Documents/Investments/portfolio.db "SELECT timestamp FROM snapshots ORDER BY id DESC LIMIT 3"

# Check for errors in logs
tail -n 50 repositories/open-agentic-investor/logs/monitor.log
```

### Automated Health Check Script
```bash
#!/bin/bash
# health_check.sh - Run from repositories/open-agentic-investor/

echo "=== Investor Health Check ==="

# Check monitor status
if pgrep -f investor_monitor > /dev/null; then
    echo "✅ Investor monitor: RUNNING"
else
    echo "❌ Investor monitor: STOPPED - restarting..."
    python scripts/investor_monitor.py >> logs/monitor.log 2>&1 &
fi

# Check recent snapshot
last_snap=$(sqlite3 ~/Documents/Investments/portfolio.db "SELECT timestamp FROM snapshots ORDER BY id DESC LIMIT 1")
if [[ -n "$last_snap" ]]; then
    echo "✅ Last snapshot: $last_snap"
else
    echo "❌ No snapshots found"
fi

# Check for errors
error_count=$(grep -i "error\|exception" logs/monitor.log | wc -l)
if [[ $error_count -gt 0 ]]; then
    echo "⚠️  Found $error_count potential errors in logs"
else
    echo "✅ No errors detected in logs"
fi

echo "=== Health Check Complete ==="
```

### Emergency Restart
If the monitor stops during your exam period:
```bash
# Kill any existing processes
pkill -f investor_monitor

# Restart with higher priority
cd repositories/open-agentic-investor && nohup python scripts/investor_monitor.py >> logs/monitor.log 2>&1 &
```

### Auto-Resume on System Restart
Add to your crontab:
```bash
# Restart investor monitor if not running (checks every 5 minutes)
*/5 * * * * pgrep -f investor_monitor || cd /home/pacificDev/.openclaw/workspace/repositories/open-agentic-investor && nohup python scripts/investor_monitor.py >> logs/monitor.log 2>&1 &
```