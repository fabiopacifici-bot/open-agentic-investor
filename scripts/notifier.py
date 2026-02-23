import os
import requests

def notify_channel(message):
    # Use environment variables for secure configuration
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", None)
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id")

    if not telegram_bot_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
        return

    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": message
    }

    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        print("Notification sent successfully")
    else:
        print(f"Failed to send notification. Status Code: {response.status_code}")

def main():
    example_message = "Stock Alert: BUY recommendation for AAPL at $150.00"
    notify_channel(example_message)

if __name__ == "__main__":
    main()