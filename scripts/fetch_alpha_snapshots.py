import requests
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

ALPHA_API_KEY = os.getenv("ALPHA_API")
BASE_URL = "https://www.alphavantage.co/query"

def fetch_alpha_snapshots(symbol, timeframe):
    """
    Fetch historical snapshots for a given symbol and timeframe from Alpha Vantage.

    :param symbol: Stock ticker symbol (e.g., NVDA, TSLA)
    :param timeframe: Time period (week, month, 3-month, etc.)
    :return: Parsed JSON data from Alpha Vantage or explicit error.
    """
    if not ALPHA_API_KEY:
        raise ValueError("Alpha Vantage API key is missing. Please set ALPHA_API in the .env file.")

    if timeframe == "week":
        function = "TIME_SERIES_WEEKLY"
        expected_info = "Weekly Prices (open, high, low, close) and Volumes"
    elif timeframe == "month":
        function = "TIME_SERIES_MONTHLY"
        expected_info = "Monthly Prices (open, high, low, close) and Volumes"
    elif timeframe in ["3-month", "6-month", "12-month", "3-year"]:
        function = "TIME_SERIES_MONTHLY"
        expected_info = "Monthly Prices (open, high, low, close) and Volumes"
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    params = {
        "function": function,
        "symbol": symbol,
        "apikey": ALPHA_API_KEY,
        "datatype": "json",
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        raise ConnectionError(f"Failed to fetch data for {symbol} ({timeframe}): {response.status_code}")

    data = response.json()

    # Error handling from Alpha Vantage's API messages
    if "Error Message" in data:
        raise ValueError(f"Alpha Vantage returned error: {data['Error Message']}")
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage Note: {data['Note']} (API limits or downtime?)")

    # Sanity check: Symbol and information type must match requested
    meta = data.get("Meta Data", {})
    actual_symbol = meta.get("2. Symbol")
    info = meta.get("1. Information")
    if actual_symbol != symbol:
        raise ValueError(f"API returned data for symbol '{actual_symbol}', but requested '{symbol}'. Possible limit or fallback.")
    if info != expected_info:
        raise ValueError(f"API returned information '{info}', but expected '{expected_info}'. Timeframe mismatch.")

    # Trim data if aggregate timeframe
    if timeframe in ["3-month", "6-month", "12-month", "3-year"]:
        num_months = int(timeframe.split("-")[0])
        series = data.get("Monthly Time Series", {})
        data["Monthly Time Series"] = dict(list(series.items())[:num_months])

    return data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fetch_alpha_snapshots.py SYMBOL TIMEFRAME")
        print("Example: python fetch_alpha_snapshots.py NVDA week")
        sys.exit(1)
    ticker = sys.argv[1]
    timeframe = sys.argv[2]
    result = fetch_alpha_snapshots(ticker, timeframe)
    print(result)
