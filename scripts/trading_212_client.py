import base64
import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Trading212Client:
    API_BASE_URL = os.getenv("API_BASE_URL", "https://demo.trading212.com/api/v0")

    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API_KEY and API_SECRET must be set in the .env file.")

        credentials = f"{self.api_key}:{self.api_secret}"
        self.auth_header = {
            "Authorization": "Basic " + base64.b64encode(credentials.encode()).decode()
        }

    def fetch_account_balance(self):
        endpoint = f"{self.API_BASE_URL}/equity/account/cash"
        response = requests.get(endpoint, headers=self.auth_header)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def place_order(self, ticker, quantity, action="BUY"):
        endpoint = f"{self.API_BASE_URL}/equity/order"
        payload = {
            "instrumentCode": ticker,
            "quantity": quantity,
            "action": action
        }
        
        response = requests.post(endpoint, json=payload, headers=self.auth_header)
        
        if response.status_code in (200, 201):
            return response.json()
        else:
            response.raise_for_status()

    def fetch_positions(self):
        endpoint = f"{self.API_BASE_URL}/positions"
        response = requests.get(endpoint, headers=self.auth_header)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

if __name__ == "__main__":
    client = Trading212Client()
    try:
        stocks = client.fetch_positions()
        print("Your Stock Holdings:", stocks)
    except Exception as e:
        print("Error fetching stocks:", e)