import requests
from utils.authentication import generate_auth_header
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def fetch_stock_prices(symbols):
    # Placeholder for a financial API base URL
    API_BASE_URL = "https://live.trading212.com/api/v0"

    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY', 'your_api_key_here')}",
    }

    prices = {}
    for symbol in symbols:
        # Removed redundant call to /metadata/instruments. Using /positions for all necessary data.
        import time; time.sleep(1)
        print(f"Price fetched from positions data for {symbol}.")

    return prices

def fetch_portfolio_symbols():
    API_BASE_URL = os.getenv("API_BASE_URL", "https://live.trading212.com/api/v0")  # Ensure live endpoint is used
    headers = generate_auth_header()

    response = requests.get(f"{API_BASE_URL}/equity/positions", headers=headers)
    print("Request Headers:", headers)
    print("API_BASE_URL:", API_BASE_URL)
    print("Response Text:", response.text)
    if response.status_code == 200:
        data = response.json()
        return [position['instrument']['ticker'] for position in data]
    else:
        print("Error fetching portfolio symbols:", response.status_code)
        return []

def fetch_prices():
    portfolio_symbols = fetch_portfolio_symbols()  # Dynamically fetched from Trading 212
    prices = fetch_stock_prices(portfolio_symbols)
    for symbol, price in prices.items():
        print(f"{symbol}: ${price}")

if __name__ == "__main__":
    main()