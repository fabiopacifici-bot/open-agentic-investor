---
name: open-agentic-investor
description: Comprehensive portfolio management, stock analysis, and notification skill for Trading212 users.
metadata:
  version: 1.0.0
---

# Open-Agentic-Investor Skill

## Overview
This skill provides a full workflow for managing a Trading212 portfolio, including:
- Fetching account and stock data.
- Analyzing portfolio performance.
- Sending actionable recommendations via notifications.

## Prerequisites
- Python 3.8+
- Virtual environment setup.
- Required environment variables in `.env`:
  ```
  API_BASE_URL=https://live.trading212.com/api/v0
  API_KEY=your_api_key_here
  API_SECRET=your_api_secret_here
  TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
  TELEGRAM_CHAT_ID=your_telegram_chat_id_here
  ```

## Usage
**Run the skill:**
```bash
python3 SKILL.py
```

**Modular commands:**
- Fetch data: `python3 SKILL.py --fetch`
- Analyze portfolio: `python3 SKILL.py --analyze`
- Send notifications: `python3 SKILL.py --notify`

## Script Workflow
1. Fetch account and stock data (`fetch_account_info.py`, `fetch_prices.py`).
2. Analyze portfolio and generate recommendations (`portfolio_manager.py`).
3. Notify user with results (`notifier.py`).

## Troubleshooting
- **401 Unauthorized Errors:** Verify API credentials in `.env`.
- **404 Errors:** Check if the API endpoints are correct or need updates.
- **Missing Notifications:** Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set correctly.

## Dashboard & Reports

### Data Directory
All data files (SQLite, HTML exports) are stored at `~/Documents/Investments/` — **never in the repo**.

### `/investor` Slash Command
Runs snapshot → generates HTML report → sends report to Telegram.

**Frequency options:** `15min` | `30min` | `1hr` | `off`

**What it does:**
1. `python -m scripts.snapshot` — fetches live data, stores to SQLite
2. `python -m scripts.report_export` — generates `~/Documents/Investments/report_<ts>.html`
3. Sends report file to Telegram via `send_report_file()`

### Start the Dashboard
```bash
cd /path/to/open-agentic-investor
python -m dashboard.app
# Open http://localhost:5001
```

### Snapshot Only
```bash
python -m scripts.snapshot
```

### Export Report Only
```bash
python -m scripts.report_export
```

### SQLite Database
- Location: `~/Documents/Investments/portfolio.db`
- Tables: `snapshots`, `positions`, `recommendations`

## Examples
**Recommendations:**
```
Ticker: AAPL
Action: BUY
Price: $150.00
```

**Notifications via Telegram:**
```
Stock Alert: BUY AAPL at $150.00
```