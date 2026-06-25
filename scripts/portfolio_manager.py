from scripts.trading_212_client import Trading212Client
from scripts.signals import calculate_rsi, calculate_sma, detect_volume_spike, check_trailing_stop_loss
from scripts.fetch_daily_history import fetch_daily_history_for_tickers
from utils.logger import logger
from datetime import datetime
import json
import os
import sqlite3

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
DB_PATH = os.environ.get(
    "INVESTMENTS_DB", os.path.expanduser("~/Documents/Investments/portfolio.db")
)


def save_portfolio_config(config: dict):
    """Atomically write config back to config.json."""
    import tempfile

    tmp_path = CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w") as f:
            json.dump(config, f, indent=4)
        os.replace(tmp_path, CONFIG_PATH)
        logger.info("config.json updated successfully")
    except Exception as e:
        logger.error(f"Failed to write config.json: {e}")
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def auto_calibrate_thresholds(positions: list, db_path: str = DB_PATH):
    """
    Auto-calibrate buy/sell thresholds based on:
    1. Position avg_price changes → set buy=avg*0.90, sell=avg*1.20
    2. Trailing stop → sell threshold = max(current sell, peak_price * 0.85)

    Skips tickers with "manual": true in config.
    """
    if not positions:
        return

    config = load_portfolio_config()
    portfolio_map = {item["symbol"]: item for item in config.get("portfolio", [])}
    changed = False

    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS avg_price_history (
            ticker          TEXT PRIMARY KEY,
            last_avg_price  REAL NOT NULL,
            updated_at      TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS price_highs (
            ticker      TEXT PRIMARY KEY,
            high        REAL NOT NULL,
            updated_at  TEXT NOT NULL
        );
    """)

    for pos in positions:
        ticker = pos.get("ticker")
        avg_price = pos.get("avg_price", 0.0) or 0.0
        current_price = pos.get("current_price", 0.0) or 0.0

        if not ticker or not avg_price or not current_price:
            continue

        cfg = portfolio_map.get(ticker)
        if not cfg:
            # New position not in config — add it
            cfg = {"symbol": ticker}
            portfolio_map[ticker] = cfg
            config["portfolio"].append(cfg)

        # Skip manual overrides
        if cfg.get("manual"):
            logger.debug(f"Skipping auto-calibrate for {ticker} (manual=true)")
            continue

        now = datetime.utcnow().isoformat()

        # --- 1. Recalibrate on avg_price change ---
        row = conn.execute(
            "SELECT last_avg_price FROM avg_price_history WHERE ticker=?", (ticker,)
        ).fetchone()
        last_avg = row[0] if row else None

        if last_avg is None or abs(avg_price - last_avg) > 0.01:
            new_buy = round(avg_price * 0.90, 2)
            new_sell = round(avg_price * 1.20, 2)

            # Only lower sell threshold if trailing stop isn't higher
            current_sell = cfg.get("sell_threshold", 0)
            if new_sell > current_sell:
                cfg["sell_threshold"] = new_sell
                changed = True
                logger.info(
                    f"Auto-calibrated {ticker}: sell=${new_sell} (avg_price={avg_price:.2f})"
                )

            cfg["buy_threshold"] = new_buy
            changed = True
            logger.info(
                f"Auto-calibrated {ticker}: buy=${new_buy} (avg_price={avg_price:.2f})"
            )

            conn.execute(
                "INSERT OR REPLACE INTO avg_price_history (ticker, last_avg_price, updated_at) VALUES (?,?,?)",
                (ticker, avg_price, now),
            )

        # --- 2. Trailing stop: sell = max(sell_threshold, peak * 0.85) ---
        peak_row = conn.execute(
            "SELECT high FROM price_highs WHERE ticker=?", (ticker,)
        ).fetchone()
        peak = peak_row[0] if peak_row else current_price

        if current_price > peak:
            peak = current_price
            conn.execute(
                "INSERT OR REPLACE INTO price_highs (ticker, high, updated_at) VALUES (?,?,?)",
                (ticker, peak, now),
            )
            logger.info(f"New peak for {ticker}: ${peak:.2f}")

        trailing_sell = round(peak * 0.85, 2)
        if trailing_sell > cfg.get("sell_threshold", 0):
            cfg["sell_threshold"] = trailing_sell
            changed = True
            logger.info(
                f"Trailing stop updated {ticker}: new sell=${trailing_sell} (peak=${peak:.2f})"
            )

    conn.commit()
    conn.close()

    if changed:
        save_portfolio_config(config)


def load_portfolio_config():
    """Load portfolio configuration with buy/sell thresholds."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            logger.info(
                f"Loaded portfolio config with {len(config.get('portfolio', []))} stocks"
            )
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"portfolio": []}


def _fetch_price_history(ticker: str, limit: int = 100) -> list:
    """Return up to *limit* daily close prices for *ticker* from price_history table.

    Prices are ordered oldest → newest (by date ASC).
    Returns an empty list if the DB or table is unavailable. Filters out NULLs and non-numeric values.
    """
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT close
            FROM price_history
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (ticker, limit),
        )
        rows = cur.fetchall()
        conn.close()
        prices = []
        for row in reversed(rows):  # reverse so oldest→newest for RSI/SMA
            v = row[0]
            if v is None:
                continue
            try:
                prices.append(float(v))
            except Exception:
                continue
        return prices
    except Exception as e:
        logger.warning(f"Could not fetch price history for {ticker}: {e}")
        return []


def _fetch_volume_history(ticker: str, limit: int = 100) -> list:
    """Return up to *limit* daily volume values for *ticker* from price_history table.

    Returns oldest → newest order and filters out NULLs.
    """
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT volume
            FROM price_history
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (ticker, limit),
        )
        rows = cur.fetchall()
        conn.close()
        volumes = []
        for row in reversed(rows):  # reverse so oldest→newest for spike detection
            v = row[0]
            if v is None:
                continue
            try:
                volumes.append(float(v))
            except Exception:
                continue
        return volumes
    except Exception as e:
        logger.warning(f"Could not fetch volume history for {ticker}: {e}")
        return []



def _fetch_thirty_day_high(ticker: str, db_path: str = DB_PATH) -> "float | None":
    """Return the highest closing price for *ticker* over the most recent 30 trading days.

    Returns None if the DB is unavailable or the ticker has no history.
    """
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT MAX(close)
            FROM (
                SELECT close
                FROM price_history
                WHERE ticker = ? AND close IS NOT NULL
                ORDER BY date DESC
                LIMIT 30
            )
            """,
            (ticker,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None or bow[0] is None:
            return None
        return float(row[0])
    except Exception as e:
        logger.warning(f"Could not fetch 30-day high for {ticker}: {e}")
        return None


def _build_indicator_reason(ticker: str, current_price: float) -> tuple:
    """Return (action_override, extra_reason) using RSI + SMA20 from historical prices and volume spikes.

    action_override is 'BUY', 'SELL', or None (fall back to threshold logic).
    extra_reason is a string to append/replace the threshold reason, or ''.
    """
    prices = _fetch_price_history(ticker)

    if len(prices) < 14:
        # Not enough data — skip indicators
        return None, ""

    rsi = calculate_rsi(prices)
    sma20 = calculate_sma(prices, period=20)

    if rsi is None:
        return None, ""

    indicator_parts = [f"RSI={rsi:.1f}"]
    if sma20 is not None:
        indicator_parts.append(f"price=€{current_price:.2f}")
        indicator_parts.append(f"SMA20=€{sma20:.2f}")

    # Check for volume spike and include in reason if present
    volumes = _fetch_volume_history(ticker)
    vol_spike = False
    if volumes:
        vol_spike = detect_volume_spike(volumes)
        if vol_spike:
            indicator_parts.append("volume_spike")

    indicator_info = ", ".join(indicator_parts)

    if rsi < 35 and sma20 is not None and current_price < sma20:
        reason = f"{indicator_info} — price below SMA20"
        return "BUY", reason

    if rsi > 70 and sma20 is not None and current_price > sma20:
        reason = f"{indicator_info} — price above SMA20"
        return "SELL", reason

    # Neutral indicator reading — no override, but include info in reason
    return None, indicator_info


def _fetch_latest_pnl_pct(ticker: str, db_path: str = DB_PATH) -> "float | None":
    """Return the most recent pnl_pct for *ticker* from the positions table, or None."""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT pnl_pct FROM positions WHERE ticker=? ORDER BY snapshot_id DESC LIMIT 1",
            (ticker,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None or row[0] is None:
            return None
        return float(row[0])
    except Exception as e:
        logger.warning(f"Could not fetch pnl_pct for {ticker}: {e}")
        return None



def _fetch_avg_price(ticker: str, db_path: str = DB_PATH) -> 'float | None':
    """Return the most recent avg_price for *ticker* from the positions table, or None."""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT avg_price FROM positions WHERE ticker=? AND avg_price > 0 ORDER BY snapshot_id DESC LIMIT 1",
            (ticker,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None or row[0] is None:
            return None
        return float(row[0])
    except Exception as e:
        logger.warning(f"Could not fetch avg_price for {ticker}: {e}")
        return None

def analyze_portfolio(account_info=None, stock_prices=None):
    """Analyze portfolio and generate buy/sell recommendations based on thresholds.

    Args:
        account_info: Account balance and metadata (optional, for future use)
        stock_prices: Dictionary of current stock prices {ticker: price}

    Returns:
        list: List of recommendation dictionaries with ticker, action, quantity, price, reason
    """
    if stock_prices is None:
        logger.warning("No stock prices provided, cannot generate recommendations")
        return []

    # Fetch fresh daily history for all tickers before analysis
    tickers = list(stock_prices.keys())
    fetch_daily_history_for_tickers(tickers)

    config = load_portfolio_config()
    portfolio_config = {item["symbol"]: item for item in config.get("portfolio", [])}

    recommendations = []

    for ticker, current_price in stock_prices.items():
        if ticker not in portfolio_config:
            logger.debug(f"No threshold config for {ticker}, skipping")
            continue

        thresholds = portfolio_config[ticker]
        buy_threshold = thresholds.get("buy_threshold")
        sell_threshold = thresholds.get("sell_threshold")

        # --- Stop-loss check (runs before threshold / indicator logic) ---
        avg_price_db = _fetch_avg_price(ticker)
        avg_price_sl = avg_price_db if (avg_price_db and avg_price_db > 0) else None
        thirty_day_high = _fetch_thirty_day_high(ticker)

        if avg_price_sl and thirty_day_high:
            sl_triggered, sl_reason, sl_type = check_trailing_stop_loss(
                current_price=current_price,
                avg_price=avg_price_sl,
                thirty_day_high=thirty_day_high,
            )
            if sl_triggered:
                loss_pct = (avg_price_sl - current_price) / avg_price_sl * 100
                full_reason = f"STOP_LOSS: {sl_reason}"
                recommendations.append(
                    {
                        "ticker": ticker,
                        "action": "SELL",
                        "quantity": 5,
                        "current_price": current_price,
                        "threshold": None,
                        "reason": full_reason,
                        "stop_loss": True,
                        "stop_type": sl_type,
                    }
                )
                logger.warning(
                    f"STOP-LOSS triggered: {ticker} SELL at ${current_price:.2f} -- {sl_reason} | Loss: {loss_pct:.1f}%"
                )
                try:
                    from scripts.notifier import notify_channel
                    alert_msg = (
                        f"🛑 STOP-LOSS triggered: {ticker} SELL at ${current_price:.2f}"
                        f" -- {sl_reason} | Loss: {loss_pct:.1f}%"
                    )
                    notify_channel(
                        alert_msg,
                        signal_key=f"STOPLOSS_{ticker}",
                        cooldown_hours=1,
                    )
                except Exception as notify_err:
                    logger.warning(f"Stop-loss Telegram alert failed: {notify_err}")
                continue  # Skip threshold/indicator logic for this ticker

        # --- Indicator-based signals ---
        indicator_action, indicator_reason = _build_indicator_reason(
            ticker, current_price
        )

        # Generate BUY recommendation if price is below buy threshold
        if buy_threshold and current_price < buy_threshold:
            base_reason = (
                f"Price ${current_price:.2f} below buy threshold ${buy_threshold:.2f}"
            )
            reason = (
                f"{base_reason} | {indicator_reason}"
                if indicator_reason
                else base_reason
            )
            recommendations.append(
                {
                    "ticker": ticker,
                    "action": "BUY",
                    "quantity": 10,  # Default quantity, can be made configurable
                    "current_price": current_price,
                    "threshold": buy_threshold,
                    "reason": reason,
                }
            )
            logger.info(f"BUY recommendation: {ticker} at ${current_price:.2f}")

        # Generate SELL recommendation if price is above sell threshold
        elif sell_threshold and current_price > sell_threshold:
            pnl_pct = _fetch_latest_pnl_pct(ticker)
            if pnl_pct is not None and pnl_pct < -5.0:
                logger.info(
                    f"SELL suppressed for {ticker}: pnl_pct={pnl_pct:.1f}% < -5%"
                )
            else:
                base_reason = f"Price ${current_price:.2f} above sell threshold ${sell_threshold:.2f}"
                reason = (
                    f"{base_reason} | {indicator_reason}"
                    if indicator_reason
                    else base_reason
                )
                recommendations.append(
                    {
                        "ticker": ticker,
                        "action": "SELL",
                        "quantity": 5,  # Default quantity, can be made configurable
                        "current_price": current_price,
                        "threshold": sell_threshold,
                        "reason": reason,
                    }
                )
                logger.info(f"SELL recommendation: {ticker} at ${current_price:.2f}")

        # No threshold trigger — check indicator-only signal
        elif indicator_action:
            if indicator_action == "SELL":
                pnl_pct = _fetch_latest_pnl_pct(ticker)
                if pnl_pct is not None and pnl_pct < -5.0:
                    logger.info(
                        f"SELL suppressed for {ticker}: pnl_pct={pnl_pct:.1f}% < -5%"
                    )
                    indicator_action = None
            if indicator_action:
                recommendations.append(
                    {
                        "ticker": ticker,
                        "action": indicator_action,
                        "quantity": 10 if indicator_action == "BUY" else 5,
                        "current_price": current_price,
                        "threshold": None,
                        "reason": indicator_reason,
                    }
                )
                logger.info(
                    f"{indicator_action} signal (indicator): {ticker} — {indicator_reason}"
                )

        else:
            logger.debug(
                f"HOLD: {ticker} at ${current_price:.2f} (buy: ${buy_threshold}, sell: ${sell_threshold})"
            )

    logger.info(f"Generated {len(recommendations)} recommendations")
    return recommendations


def main():
    """Standalone execution to analyze portfolio and optionally execute orders."""
    from scripts.fetch_prices import fetch_stock_prices
    from scripts.fetch_account_info import fetch_account_info

    try:
        # Fetch current data
        logger.info("Fetching account info...")
        account_info = fetch_account_info()

        logger.info("Fetching stock prices...")
        stock_prices = fetch_stock_prices()

        # Analyze and get recommendations
        logger.info("Analyzing portfolio...")
        recommendations = analyze_portfolio(account_info, stock_prices)

        if not recommendations:
            print("No buy/sell recommendations at this time.")
            return

        # Display recommendations
        print("\n=== Portfolio Recommendations ===")
        for rec in recommendations:
            print(f"\n{rec['action']} {rec['ticker']}")
            print(f"  Current Price: ${rec['current_price']:.2f}")
            threshold_display = (
                f"${rec['threshold']:.2f}" if rec["threshold"] is not None else "N/A"
            )
            print(f"  Threshold: {threshold_display}")
            print(f"  Quantity: {rec['quantity']}")
            print(f"  Reason: {rec['reason']}")

        # Ask for confirmation before placing orders
        response = input("\nExecute these orders? (yes/no): ").strip().lower()

        if response == "yes":
            client = Trading212Client()
            for rec in recommendations:
                try:
                    order_response = client.place_order(
                        ticker=rec["ticker"],
                        quantity=rec["quantity"],
                        action=rec["action"],
                    )
                    print(
                        f"✓ Order placed for {rec['ticker']} ({rec['action']}):",
                        order_response,
                    )
                except Exception as e:
                    logger.error(f"Error placing order for {rec['ticker']}: {e}")
                    print(f"✗ Error placing order for {rec['ticker']}: {e}")
        else:
            print("Orders cancelled by user.")

    except Exception as e:
        logger.error(f"Error in portfolio analysis: {e}")
        raise


if __name__ == "__main__":
    main()
