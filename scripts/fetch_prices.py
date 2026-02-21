import requests
import os

def fetch_stock_prices(symbols):
    # Placeholder for a financial API base URL
    API_BASE_URL = "https://financialapi.com/stock/price"

    headers = {
        "Authorization": f"Bearer {os.getenv('FINANCIAL_API_KEY', 'your_api_key_here')}"
    }

    prices = {}
    for symbol in symbols:
        response = requests.get(f"{API_BASE_URL}/{symbol}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            prices[symbol] = data.get("price", None)
        else:
            print(f"Failed to fetch price for {symbol}:", response.status_code)

    return prices

def main():
    portfolio_symbols = ["AAPL", "TSLA", "GOOG"]  # Example symbols
    prices = fetch_stock_prices(portfolio_symbols)
    for symbol, price in prices.items():
        print(f"{symbol}: ${price}")

if __name__ == "__main__":
    main()