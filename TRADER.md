# TRADER.md - Open-Agentic-Investor Documentation

## Purpose
This document captures a comprehensive understanding of the Open-Agentic-Investor skill. It explains available scripts, their purpose, and their interaction in the workflow, based on the repository's files.

---

## Script Overview

1. **fetch_account_info.py**
   - Fetches account balance using the `Trading212Client`.
   - Primary purpose: Retrieve and display the user's account cash balance.
   - Example usage::
     ```bash
     python scripts/fetch_account_info.py
     ```

2. **fetch_alpha_snapshots.py**
   - Retrieves historical snapshots for a given stock (symbol) over specified timeframes via the Alpha Vantage API.
   - Requires a valid `ALPHA_API_KEY` in the `.env`.
   - Timeframes supported: week, month, or multi-month windows.
   - Example usage:
     ```bash
     python scripts/fetch_alpha_snapshots.py
     ```

3. **fetch_prices.py**
   - Retrieves real-time stock prices. Portfolio symbols are dynamically fetched from Trading212.
   - Key functions:
     - `fetch_portfolio_symbols`: Retrieves portfolio tickers.
     - `fetch_stock_prices`: Collects price data for each ticker.
   - Example usage:
     ```bash
     python scripts/fetch_prices.py
     ```

4. **main.py**
   - Orchestrates the workflow by invoking all major scripts.
   - Workflow steps include:
     1. Fetch account information.
     2. Fetch stock prices.
     3. Analyze portfolio.
     4. Send notifications with recommendations.
   - Example usage:
     ```bash
     python scripts/main.py
     ```

5. **notifier.py**
   - Sends notifications via Telegram.
   - Requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the `.env` file.
   - Endpoint: `https://api.telegram.org/bot<TOKEN>/sendMessage`.
   - Example usage:
     ```bash
     python scripts/notifier.py
     ```

6. **place_order.py**
   - Interacts with the Trading212 API to place stock orders.
   - Prompts user input (e.g., ticker, quantity, action).
   - Example usage:
     ```bash
     python scripts/place_order.py
     ```

7. **portfolio_manager.py**
   - Analyzes the portfolio and defines recommendations for orders (e.g., BUY/SELL).
   - Example output:
     ```plaintext
     Recommendations:
     - Ticker: AAPL, Action: BUY, Quantity: 10
     ```
   - Example usage:
     ```bash
     python scripts/portfolio_manager.py
     ```

8. **trading_212_client.py**
   - Core API client for Trading212.
   - Functions:
     1. Fetch account balance (`fetch_account_balance`).
     2. Place orders (`place_order`).
   - Example integration method:
     ```python
     client = Trading212Client()
     balance = client.fetch_account_balance()
     client.place_order(ticker="AAPL", quantity=1, action="BUY")
     ```

---

## Example Workflow

1. **Fetch Data:** Retrieve portfolio symbols and stock prices.
   ```bash
   python scripts/fetch_prices.py
   ```

2. **Analyze Portfolio:** Generate insights and recommendations.
   ```bash
   python scripts/portfolio_manager.py
   ```

3. **Notify:** Send generated recommendations via Telegram.
   ```bash
   python scripts/notifier.py
   ```

4. **Execute Orders:** Automatically place orders.
   ```bash
   python scripts/place_order.py
   ```

5. **Full Integration:** Run everything sequentially.
   ```bash
   python scripts/main.py
   ```

---

## Notes
- Ensure all necessary API keys and tokens are configured properly in the `.env` file.
- The script uses modular design, meaning each function can be extended or replaced easily to suit specific requirements.