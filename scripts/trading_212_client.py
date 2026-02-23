import os
import requests
from credential_handler import get_credential
from utils.logger import logger

class Trading212Client:
    def __init__(self):
        # Load credentials at runtime (after .env has been loaded by credential handler)
        self.api_key = get_credential("API_KEY")

        # Resolve API base URL at runtime so environment overrides take effect
        self.api_base_url = os.getenv("API_BASE_URL", "https://live.trading212.com/api/v0")

        from utils.authentication import generate_auth_header
        self.auth_header = generate_auth_header()

    def fetch_account_balance(self):
        """Fetch account cash balance from Trading 212 API.
        
        Returns:
            dict: Account balance information
            
        Raises:
            requests.HTTPError: If API request fails
        """
        endpoint = f"{self.api_base_url}/equity/account/cash"
        logger.info("Fetching account balance...")
        
        try:
            response = requests.get(endpoint, headers=self.auth_header, timeout=30)
            logger.debug(f"Request Headers: {self.auth_header}")
            logger.debug(f"Endpoint: {endpoint}")

            if response.status_code == 200:
                logger.info("Account balance retrieved successfully.")
                return response.json()
            else:
                logger.error(f"Failed to fetch account balance: {response.status_code} {response.text}")
                logger.debug(f"Response headers: {response.headers}")
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error fetching account balance: {e}")
            raise

    def place_order(self, ticker, quantity, action="BUY"):
        """Place a market order on Trading 212.
        
        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares to buy/sell
            action: "BUY" or "SELL"
            
        Returns:
            dict: Order response from API
            
        Raises:
            requests.HTTPError: If order placement fails
        """
        endpoint = f"{self.api_base_url}/equity/orders/market"
        payload = {
            "instrumentCode": ticker,
            "quantity": abs(quantity),  # Ensure positive quantity
            "timeValidity": "DAY"
        }

        logger.info(f"Placing {action} order for {ticker} - Quantity: {quantity}")
        logger.debug(f"Order payload: {payload}")
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.auth_header, timeout=30)

            if response.status_code in (200, 201):
                logger.info(f"{action} order placed successfully for {ticker}.")
                return response.json()
            else:
                logger.error(f"Order failed: {response.status_code} {response.text}")
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error placing order: {e}")
            raise