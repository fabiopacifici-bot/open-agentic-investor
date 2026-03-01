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
    # Short-circuit outbound network calls when NO_OUTBOUND env var is set (used in testing/subagent runs)
    if os.getenv('NO_OUTBOUND', '').lower() in ('1','true','yes'):
        print('notify_channel: NO_OUTBOUND set — skipping network call')
        return True

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

def send_report_file(filepath: str, caption: str = "📊 Portfolio Report") -> bool:
    """Send an HTML report file to Telegram as a document attachment.

    Args:
        filepath: Path to the HTML file to send.
        caption: Caption text shown with the file.

    Returns:
        bool: True if sent successfully.
    """
    if os.getenv('NO_OUTBOUND', '').lower() in ('1', 'true', 'yes'):
        print(f'send_report_file: NO_OUTBOUND set — skipping network call (file: {filepath})')
        return True

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    if not telegram_chat_id:
        raise ValueError("TELEGRAM_CHAT_ID not set")

    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                api_url,
                data={"chat_id": telegram_chat_id, "caption": caption},
                files={"document": (os.path.basename(filepath), f, "text/html")},
                timeout=30,
            )
        if response.status_code == 200:
            logger.info(f"Report file sent: {filepath}")
            return True
        else:
            logger.error(f"Failed to send report file: {response.status_code} {response.text}")
            response.raise_for_status()
            return False
    except requests.RequestException as e:
        logger.error(f"Network error sending report file: {e}")
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
