import os

def get_credential(key):
    """Fetches credentials dynamically from environment or OpenClaw secure token backend."""
    # Prefer .env value
    value = os.getenv(key)
    if value:
        return value

    # Dynamically prompt user as fallback
    # Example: Prompt user for runtime injection
    # Replace this with OpenClaw secure backend API call if available
    return input(f"Please provide your {key}: ")