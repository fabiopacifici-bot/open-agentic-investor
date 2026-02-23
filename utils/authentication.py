import os
import base64
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

class AuthenticationError(Exception):
    pass

def load_credentials():
    """Load API credentials from environment variables.
    
    Trading 212 API uses HTTP Basic Authentication:
    - API Key as username
    - API Secret as password
    - Encoded as Base64 with "Basic " prefix
    """
    api_base_url = os.getenv("API_BASE_URL")
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    if not all([api_base_url, api_key, api_secret]):
        raise AuthenticationError("Missing required API credentials (API_BASE_URL, API_KEY, API_SECRET) in environment variables.")

    return {
        "api_base_url": api_base_url,
        "api_key": api_key,
        "api_secret": api_secret
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
    
    Trading 212 uses HTTP Basic Authentication:
    1. Combine API_KEY:API_SECRET
    2. Base64 encode the combined string
    3. Prepend with "Basic "
    
    Authorization: Basic {base64_encoded_credentials}
    
    Returns:
        dict: Headers dictionary with Authorization
    """
    creds = load_credentials()
    
    # 1. Combine API key and secret with colon separator
    credentials_string = f"{creds['api_key']}:{creds['api_secret']}"
    
    # 2. Encode to bytes, then Base64 encode
    encoded_credentials = base64.b64encode(credentials_string.encode('utf-8')).decode('utf-8')
    
    # 3. Prepend with "Basic "
    auth_value = f"Basic {encoded_credentials}"
    
    return {
        "Authorization": auth_value,
        "Content-Type": "application/json"
    }