import base64
import os
import requests
from credential_handler import get_credential
from utils.logger import logger

class Trading212Client:
    def __init__(self):
        # Load credentials at runtime (after .env has been loaded by credential handler)
        self.api_key = get_credential("API_KEY")
        self.api_secret = get_credential("API_SECRET")

        # Resolve API base URL at runtime so environment overrides take effect
        self.api_base_url = os.getenv("API_BASE_URL", "https://demo.trading212.com/api/v0")

        from utils.authentication import generate_auth_header
        self.auth_header = generate_auth_header()

    def fetch_account_balance(self):
        endpoint = f"{self.api_base_url}/equity/account/cash"
        logger.info("Fetching account balance...")
        response = requests.get(endpoint, headers=self.auth_header)
        logger.debug(f"Request Headers: {self.auth_header}")
        logger.debug(f"Endpoint: {endpoint}")

        if response.status_code == 200:
            logger.info("Account balance retrieved successfully.")
            return response.json()
        else:
            logger.error(f"Failed to fetch account balance: {response.status_code} {response.text}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response content (bytes): {response.content}")
            response.raise_for_status()

    def place_order(self, ticker, quantity, action="BUY"):
        endpoint = f"{self.api_base_url}/equity/order"
        payload = {
            "instrumentCode": ticker,
            "quantity": quantity,
            "action": action
        }

        logger.info(f"Placing order for {ticker} - Action: {action}, Quantity: {quantity}")
        response = requests.post(endpoint, json=payload, headers=self.auth_header)

        if response.status_code in (200, 201):
            logger.info("Order placed successfully.")
            return response.json()
        else:
            logger.error(f"Order failed: {response.status_code} {response.text}")
            response.raise_for_status()