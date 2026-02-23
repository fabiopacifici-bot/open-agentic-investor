import base64
import os
import requests
from dotenv import load_dotenv
from utils.logger import logger

# Load .env file
load_dotenv()

class Trading212Client:
    API_BASE_URL = os.getenv("API_BASE_URL", "https://demo.trading212.com/api/v0")

    def __init__(self):
        from utils.authentication import load_credentials
        creds = load_credentials()
        self.api_key = creds["api_key"]
        self.api_secret = creds["api_secret"]

        credentials = f"{self.api_key}:{self.api_secret}"
        from utils.authentication import generate_auth_header
        self.auth_header = generate_auth_header()

    def fetch_account_balance(self):
        endpoint = f"{self.API_BASE_URL}/equity/account/cash"
        logger.info("Fetching account balance...")
        response = requests.get(endpoint, headers=self.auth_header)
        logger.debug(f"Request Headers: {self.auth_header}")
        logger.debug(f"Endpoint: {endpoint}")

        if response.status_code == 200:
            logger.info("Account balance retrieved successfully.")
            return response.json()
        else:
            logger.error(f"Failed to fetch account balance: {response.status_code} {response.text}")
            response.raise_for_status()

    def place_order(self, ticker, quantity, action="BUY"):
        endpoint = f"{self.API_BASE_URL}/equity/order"
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
            logger.error(f"Failed to place order: {response.status_code} {response.text}")
            response.raise_for_status()