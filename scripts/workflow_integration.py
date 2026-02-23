from fetch_alpha_snapshots import fetch_alpha_snapshots
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to analyze positions and fetch historical snapshots
def analyze_positions_with_snapshots(positions):
    """
    Analyze stock positions and fetch historical snapshots from Alpha Vantage.

    :param positions: List of position metadata (symbols, volatility, gains/losses).
    :return: Analysis report based on fetched data.
    """
    analysis_report = []

    for pos in positions:
        symbol = pos.get("symbol")
        volatility = pos.get("volatility")
        unrealized_gains = pos.get("unrealized_gains")

        logging.info(f"Analyzing position for symbol: {symbol}")

        # Decide timeframe based on volatility and gains
        if volatility > 1.5 or unrealized_gains < -5:
            timeframe = "week"
        elif -5 <= unrealized_gains <= 5:
            timeframe = "month"
        else:
            timeframe = "3-month"

        logging.info(f"Fetching historical data for {symbol} with timeframe: {timeframe}")

        try:
            snapshots = fetch_alpha_snapshots(symbol, timeframe)
            analysis_report.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "snapshots": snapshots
            })
        except Exception as e:
            logging.error(f"Failed to fetch data for {symbol}: {str(e)}")

    return analysis_report

# Example usage
if __name__ == "__main__":
    # Example positions metadata
    positions = [
        {"symbol": "AAPL", "volatility": 1.2, "unrealized_gains": -2},
        {"symbol": "TSLA", "volatility": 2.1, "unrealized_gains": -6},
        {"symbol": "MSFT", "volatility": 0.8, "unrealized_gains": 3},
    ]

    result = analyze_positions_with_snapshots(positions)
    print(json.dumps(result, indent=2))