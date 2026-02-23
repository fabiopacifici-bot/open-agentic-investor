from scripts.trading_212_client import Trading212Client
from utils.logger import logger
import json
import os

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
        
        # Generate BUY recommendation if price is below buy threshold
        if buy_threshold and current_price < buy_threshold:
            recommendations.append({
                "ticker": ticker,
                "action": "BUY",
                "quantity": 10,  # Default quantity, can be made configurable
                "current_price": current_price,
                "threshold": buy_threshold,
                "reason": f"Price ${current_price:.2f} below buy threshold ${buy_threshold:.2f}"
            })
            logger.info(f"BUY recommendation: {ticker} at ${current_price:.2f}")
        
        # Generate SELL recommendation if price is above sell threshold
        elif sell_threshold and current_price > sell_threshold:
            recommendations.append({
                "ticker": ticker,
                "action": "SELL",
                "quantity": 5,  # Default quantity, can be made configurable
                "current_price": current_price,
                "threshold": sell_threshold,
                "reason": f"Price ${current_price:.2f} above sell threshold ${sell_threshold:.2f}"
            })
            logger.info(f"SELL recommendation: {ticker} at ${current_price:.2f}")
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