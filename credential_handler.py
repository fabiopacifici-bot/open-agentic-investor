import os
from dotenv import load_dotenv

# Ensure .env file is loaded
def load_environment():
    dotenv_path = os.path.join(os.getcwd(), ".env")
    success = load_dotenv(dotenv_path=dotenv_path)
    if success:
        print(f"Successfully loaded .env file from {dotenv_path}")
    else:
        print(f"Warning: Could not find .env file at {dotenv_path}")
        print("Will attempt to use existing environment variables")

def get_credential(key):
    """Fetches credentials dynamically from environment or OpenClaw secure token backend.
    
    Args:
        key: The environment variable key to retrieve
    
    Returns:
        str: The credential value
    
    Raises:
        ValueError: If credential is not found and cannot be provided
    """
    # Load .env variables
    load_environment()
    
    # Prefer .env value
    value = os.getenv(key)
    if value:
        # Don't print actual values for security (especially API keys)
        print(f"DEBUG: Retrieved {key} from environment")
        return value

    # Dynamically prompt user as fallback
    # Replace this with OpenClaw secure backend API call if available
    print(f"Warning: {key} not found in environment variables")
    value = input(f"Please provide your {key}: ").strip()
    
    if not value:
        raise ValueError(f"Credential {key} is required but not provided")
    
    return value