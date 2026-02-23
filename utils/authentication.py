import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

class AuthenticationError(Exception):
    pass

def load_credentials():
    """Load API credentials from environment variables.
    
    Trading 212 API may use either:
    - Simple API Key in Authorization header, OR
    - API Key + API Secret (depending on your account setup)
    """
    api_base_url = os.getenv("API_BASE_URL")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")  # Optional, depends on Trading 212 setup

    if not all([api_base_url, api_key]):
        raise AuthenticationError("Missing required API credentials (API_BASE_URL, API_KEY) in environment variables.")

    return {
        "api_base_url": api_base_url,
        "api_key": api_key,
        "api_secret": api_secret  # May be None if not provided
    }

def validate_token(auth_header):
    """Validate API token by making a test request to account endpoint.
    
    Args:
        auth_header: Dictionary with Authorization header
    
    Returns:
        bool: True if token is valid
    
    Raises:
        AuthenticationError: If token is invalid or request fails
    """
    creds = load_credentials()
    endpoint = f"{creds['api_base_url']}/equity/account/cash"
    
    try:
        response = requests.get(endpoint, headers=auth_header, timeout=10)
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            raise AuthenticationError("Invalid API key or unauthorized access.")
        else:
            raise AuthenticationError(f"Token validation failed with status {response.status_code}")
    except requests.RequestException as e:
        raise AuthenticationError(f"Network error during token validation: {e}")

def generate_auth_header():
    """Generate authentication header for Trading 212 API requests.
    
    Supports two authentication methods:
    1. Simple API Key: Authorization: {API_KEY}
    2. API Key + Secret (if both provided): Authorization: {API_KEY}:{API_SECRET}
    
    Returns:
        dict: Headers dictionary with Authorization
    """
    creds = load_credentials()
    
    # If API_SECRET is provided, combine with API_KEY
    if creds['api_secret']:
        auth_value = f"{creds['api_key']}:{creds['api_secret']}"
    else:
        auth_value = creds['api_key']
    
    return {
        "Authorization": auth_value,
        "Content-Type": "application/json"
    }