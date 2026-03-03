import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_channel_config(channel: str, key: str) -> str:
    """Retrieves user-preferred channel settings dynamically from environment.
    
    Args:
        channel: Channel type (e.g., 'telegram', 'slack')
        key: Config key to retrieve (e.g., 'botToken', 'chatId')
        
    Returns:
        str: Configuration value from environment, or None if not found
    """
    if channel == "telegram" and key == "botToken":
        return os.getenv("TELEGRAM_BOT_TOKEN")
    if channel == "telegram" and key == "chatId":
        return os.getenv("TELEGRAM_CHAT_ID")
    
    # Generic lookup for other channel types
    env_key = f"{channel.upper()}_{key.upper()}"
    return os.getenv(env_key)

def validate_channel_config(channel: str) -> bool:
    """Validate that required channel configuration is present.
    
    Args:
        channel: Channel type to validate
        
    Returns:
        bool: True if configuration is complete, False otherwise
    """
    if channel == "telegram":
        bot_token = get_channel_config("telegram", "botToken")
        chat_id = get_channel_config("telegram", "chatId")
        return bool(bot_token and chat_id)
    
    return False