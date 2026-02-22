import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def fetch_stock_prices(symbols):
    # Placeholder for a financial API base URL
    API_BASE_URL = "https://www.alphavantage.co/query"

    headers = {
        "Authorization": f"Bearer {os.getenv('FINANCIAL_API_KEY', 'your_api_key_here')}",
    }

    prices = {}
    for symbol in symbols:
        response = requests.get(f"{API_BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={headers['Authorization']}")
        import time; time.sleep(1)
        if response.status_code == 200:
            data = response.json()
            print("Raw API Response:", data)
            prices[symbol] = data.get("Global Quote", {}).get("05. price", None)
        else:
            print(f"Failed to fetch price for {symbol}:", response.status_code)

    return prices

def fetch_portfolio_symbols():
    API_BASE_URL = "https://live.trading212.com/api/v0"  # Ensure live endpoint is used
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
    }

    response = requests.get(f"{API_BASE_URL}/equity/portfolio", headers=headers)
    print("Request Headers:", headers)
    print("API_BASE_URL:", API_BASE_URL)
    print("Response Text:", response.text)
    if response.status_code == 200:
        data = response.json()
        return [stock['symbol'] for stock in data.get('portfolio', [])]
    else:
        print("Error fetching portfolio symbols:", response.status_code)
        return []

def main():
    portfolio_symbols = fetch_portfolio_symbols()  # Dynamically fetched from Trading 212
    prices = fetch_stock_prices(portfolio_symbols)
    for symbol, price in prices.items():
        print(f"{symbol}: ${price}")

if __name__ == "__main__":
    main()