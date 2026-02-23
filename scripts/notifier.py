import os
import requests
from utils.logger import logger

def notify_channel(message):
    """Send notification message via Telegram.
    
    Args:
        message: Message text to send (can be string or dict/list that will be formatted)
        
    Returns:
        bool: True if notification sent successfully, False otherwise
        
    Raises:
        ValueError: If TELEGRAM_BOT_TOKEN is not configured
        requests.HTTPError: If Telegram API request fails
    """
    # Use environment variables for secure configuration
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", None)
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", None)

    if not telegram_bot_token:
        error_msg = "Error: TELEGRAM_BOT_TOKEN environment variable is not set."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    if not telegram_chat_id:
        error_msg = "Error: TELEGRAM_CHAT_ID environment variable is not set."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Format message if it's a list of recommendations
    if isinstance(message, list):
        if not message:
            formatted_message = "✓ Portfolio analyzed - No recommendations at this time."
        else:
            formatted_message = "\n📊 *Trading Recommendations* \n\n"
            for rec in message:
                action_emoji = "🟢" if rec.get('action') == 'BUY' else "🔴"
                formatted_message += f"{action_emoji} *{rec.get('action')} {rec.get('ticker')}*\n"
                formatted_message += f"   Price: ${rec.get('current_price', 0):.2f}\n"
                formatted_message += f"   Quantity: {rec.get('quantity', 0)}\n"
                formatted_message += f"   Reason: {rec.get('reason', 'N/A')}\n\n"
    else:
        formatted_message = str(message)

    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": formatted_message,
        "parse_mode": "Markdown"
    }

    try:
        logger.info(f"Sending notification to Telegram chat {telegram_chat_id}")
        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("Notification sent successfully")
            print("✓ Notification sent successfully")
            return True
        else:
            error_msg = f"Failed to send notification. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            print(f"✗ {error_msg}")
            response.raise_for_status()
            return False
    except requests.RequestException as e:
        error_msg = f"Network error sending notification: {e}"
        logger.error(error_msg)
        raise

def main():
    """Test notification function."""
    example_message = "Stock Alert: BUY recommendation for AAPL at $150.00"
    try:
        notify_channel(example_message)
    except Exception as e:
        logger.error(f"Error in notifier test: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()