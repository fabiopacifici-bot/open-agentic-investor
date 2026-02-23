import os
from dotenv import load_dotenv

# Ensure .env file is loaded
def load_environment():
    dotenv_path = os.path.join(os.getcwd(), ".env")
    success = load_dotenv(dotenv_path=dotenv_path)
    if success:
        print(f"Successfully loaded .env file from {dotenv_path}")
    else:
        print(f"Failed to load .env file from {dotenv_path}")

def get_credential(key):
    """Fetches credentials dynamically from environment or OpenClaw secure token backend."""
    # Load .env variables
    load_environment()
    
    # Prefer .env value
    value = os.getenv(key)
    print(f"DEBUG: Retrieved {key} = {value}")
    if value:
        return value

    # Dynamically prompt user as fallback
    # Example: Prompt user for runtime injection
    # Replace this with OpenClaw secure backend API call if available
    return input(f"Please provide your {key}: ")