import os
from dotenv import load_dotenv
import logging
import requests

# Load environment variables
load_dotenv()

class AuthenticationError(Exception):
    pass

def load_credentials():
    """Load API credentials from environment variables."""
    api_base_url = os.getenv("API_BASE_URL")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    if not all([api_base_url, api_key, api_secret]):
        raise AuthenticationError("Missing one or more required API credentials in environment variables.")

    return {
        "api_base_url": api_base_url,
        "api_key": api_key,
        "api_secret": api_secret
    }

def validate_token(auth_header):
    """Validate API token by making a lightweight API request."""
    endpoint = f"{load_credentials()['api_base_url']}/validate-token"
    response = requests.get(endpoint, headers=auth_header)

    if response.status_code != 200:
        raise AuthenticationError("Invalid API token or unauthorized access.")

    return True

def generate_auth_header():
    """Generate authentication header for API requests."""
    creds = load_credentials()
    auth_token = f"{creds['api_key']}:{creds['api_secret']}"
    return {
        "Authorization": f"Basic {auth_token}"
    }