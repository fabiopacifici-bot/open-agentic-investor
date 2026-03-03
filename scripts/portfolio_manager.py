from scripts.trading_212_client import Trading212Client
from scripts.signals import calculate_rsi, calculate_sma, detect_volume_spike
from utils.logger import logger
import json
import os
import sqlite3

def load_portfolio_config():
    """Load portfolio configuration with buy/sell thresholds."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info(f"Loaded portfolio config with {len(config.get('portfolio', []))} stocks")
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"portfolio": []}

DB_PATH = os.path.expanduser("~/Documents/Investments/portfolio.db")


def _fetch_price_history(ticker: str, limit: int = 30) -> list:
    """Return up to *limit* historical current_price values for *ticker* from portfolio.db.

    Prices are ordered oldest → newest (by snapshot_id).
    Returns an empty list if the DB or table is unavailable. Filters out NULLs and non-numeric values.
    """
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT current_price
            FROM positions
            WHERE ticker = ?
            ORDER BY snapshot_id DESC
            LIMIT ?
            """,
            (ticker, limit),
        )
        rows = cur.fetchall()
        conn.close()
        # Reverse so we get oldest → newest and coerce to floats, dropping NULLs
        prices = []
        for row in reversed(rows):
            v = row[0]
            if v is None:
                continue
            try:
                prices.append(float(v))
            except Exception:
                # Skip non-numeric entries
                continue
        return prices
    except Exception as e:
        logger.warning(f"Could not fetch price history for {ticker}: {e}")
        return []


def _fetch_volume_history(ticker: str, limit: int = 30) -> list:
    """Attempt to fetch historical volume values for ticker from portfolio.db.

    The positions table may store volume; this helper will return an empty list when no volume column exists.
    Returns oldest → newest order and filters out NULLs.
    """
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # Check if volume column exists
        cur.execute("PRAGMA table_info(positions)")
        cols = [r[1] for r in cur.fetchall()]
        if 'volume' not in cols:
            conn.close()
            return []

        cur.execute(
            """
            SELECT volume
            FROM positions
            WHERE ticker = ?
            ORDER BY snapshot_id DESC
            LIMIT ?
            """,
            (ticker, limit),
        )
        rows = cur.fetchall()
        conn.close()
        volumes = []
        for row in reversed(rows):
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
    
    config = load_portfolio_config()
    portfolio_config = {item['symbol']: item for item in config.get('portfolio', [])}
    
    recommendations = []
    
    for ticker, current_price in stock_prices.items():
        if ticker not in portfolio_config:
            logger.debug(f"No threshold config for {ticker}, skipping")
            continue
        
        thresholds = portfolio_config[ticker]
        buy_threshold = thresholds.get('buy_threshold')
        sell_threshold = thresholds.get('sell_threshold')
        
        # --- Indicator-based signals ---
        indicator_action, indicator_reason = _build_indicator_reason(ticker, current_price)

        # Generate BUY recommendation if price is below buy threshold
        if buy_threshold and current_price < buy_threshold:
            base_reason = f"Price ${current_price:.2f} below buy threshold ${buy_threshold:.2f}"
            reason = f"{base_reason} | {indicator_reason}" if indicator_reason else base_reason
            recommendations.append({
                "ticker": ticker,
                "action": "BUY",
                "quantity": 10,  # Default quantity, can be made configurable
                "current_price": current_price,
                "threshold": buy_threshold,
                "reason": reason,
            })
            logger.info(f"BUY recommendation: {ticker} at ${current_price:.2f}")

        # Generate SELL recommendation if price is above sell threshold
        elif sell_threshold and current_price > sell_threshold:
            base_reason = f"Price ${current_price:.2f} above sell threshold ${sell_threshold:.2f}"
            reason = f"{base_reason} | {indicator_reason}" if indicator_reason else base_reason
            recommendations.append({
                "ticker": ticker,
                "action": "SELL",
                "quantity": 5,  # Default quantity, can be made configurable
                "current_price": current_price,
                "threshold": sell_threshold,
                "reason": reason,
            })
            logger.info(f"SELL recommendation: {ticker} at ${current_price:.2f}")

        # No threshold trigger — check indicator-only signal
        elif indicator_action:
            recommendations.append({
                "ticker": ticker,
                "action": indicator_action,
                "quantity": 10 if indicator_action == "BUY" else 5,
                "current_price": current_price,
                "threshold": None,
                "reason": indicator_reason,
            })
            logger.info(f"{indicator_action} signal (indicator): {ticker} — {indicator_reason}")

        else:
            logger.debug(f"HOLD: {ticker} at ${current_price:.2f} (buy: ${buy_threshold}, sell: ${sell_threshold})")
    
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
            print(f"  Threshold: ${rec['threshold']:.2f}")
            print(f"  Quantity: {rec['quantity']}")
            print(f"  Reason: {rec['reason']}")
        
        # Ask for confirmation before placing orders
        response = input("\nExecute these orders? (yes/no): ").strip().lower()
        
        if response == 'yes':
            client = Trading212Client()
            for rec in recommendations:
                try:
                    order_response = client.place_order(
                        ticker=rec["ticker"],
                        quantity=rec["quantity"],
                        action=rec["action"]
                    )
                    print(f"✓ Order placed for {rec['ticker']} ({rec['action']}):", order_response)
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
