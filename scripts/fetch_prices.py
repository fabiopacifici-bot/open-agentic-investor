import requests
from utils.authentication import generate_auth_header
import os
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables from .env
load_dotenv()

def fetch_portfolio_data():
    """Fetch complete portfolio data from Trading 212 API."""
    API_BASE_URL = os.getenv("API_BASE_URL", "https://live.trading212.com/api/v0")
    headers = generate_auth_header()

    endpoint = f"{API_BASE_URL}/equity/portfolio"
    logger.info(f"Fetching portfolio data from {endpoint}")
    
    response = requests.get(endpoint, headers=headers)
    logger.debug(f"Request Headers: {headers}")
    logger.debug(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info("Portfolio data retrieved successfully.")
        return data
    else:
        logger.error(f"Error fetching portfolio: {response.status_code} {response.text}")
        response.raise_for_status()

def fetch_stock_prices():
    """Extract current stock prices from portfolio positions.
    
    Returns:
        dict: Dictionary mapping ticker symbols to current prices
    """
    portfolio = fetch_portfolio_data()
    prices = {}
    
    # Extract prices from positions
    if isinstance(portfolio, dict):
        positions = portfolio.get('positions', [])
    elif isinstance(portfolio, list):
        positions = portfolio
    else:
        positions = []

    for position in positions:
        ticker = position.get('ticker')
        current_price = position.get('currentPrice')
        
        if ticker and current_price:
            prices[ticker] = current_price
            logger.info(f"{ticker}: ${current_price:.2f}")
    
    return prices

def fetch_prices():
    """Main function to fetch and display stock prices."""
    prices = fetch_stock_prices()
    
    if prices:
        print("\n=== Current Stock Prices ===")
        for symbol, price in prices.items():
            print(f"{symbol}: ${price:.2f}")
        print(f"\nTotal positions: {len(prices)}")
    else:
        print("No positions found or unable to fetch prices.")
    
    return prices

def main():
    """Entry point for standalone execution."""
    try:
        fetch_prices()
    except Exception as e:
        logger.error(f"Error in fetch_prices: {e}")
        raise

if __name__ == "__main__":
    main()