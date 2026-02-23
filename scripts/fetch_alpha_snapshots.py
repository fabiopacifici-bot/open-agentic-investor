import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

ALPHA_API_KEY = os.getenv("ALPHA_API")
BASE_URL = "https://www.alphavantage.co/query"

def fetch_alpha_snapshots(symbol, timeframe):
    """
    Fetch historical snapshots for a given symbol and timeframe from Alpha Vantage.

    :param symbol: Stock ticker symbol (e.g., AAPL, TSLA)
    :param timeframe: Time period (e.g., week, month, 3-month, etc.)
    :return: Parsed JSON data from Alpha Vantage.
    """
    if not ALPHA_API_KEY:
        raise ValueError("Alpha Vantage API key is missing. Please set ALPHA_API in the .env file.")

    # Determine the endpoint and parameters based on the timeframe
    if timeframe == "week":
        function = "TIME_SERIES_WEEKLY"
    elif timeframe == "month":
        function = "TIME_SERIES_MONTHLY"
    elif timeframe in ["3-month", "6-month", "12-month", "3-year"]:
        function = "TIME_SERIES_MONTHLY"
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

    if timeframe in ["3-month", "6-month", "12-month", "3-year"]:
        # Extract specific rows based on the timeframe
        num_months = int(timeframe.split("-")[0])
        data = dict(list(data["Monthly Time Series"].items())[:num_months])

    return data

if __name__ == "__main__":
    # Example Usage
    ticker = "AAPL"
    timeframe = "month"
    snapshot = fetch_alpha_snapshots(ticker, timeframe)
    print(snapshot)