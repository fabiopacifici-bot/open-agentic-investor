import logging
from scripts.fetch_account_info import fetch_account_info
from scripts.fetch_prices import fetch_prices
from scripts.portfolio_manager import analyze_portfolio
from scripts.notifier import notify_channel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("entry_point")

def main():
    try:
        logger.info("Fetching account information...")
        account_info = fetch_account_info()

        logger.info("Fetching stock prices...")
        stock_prices = fetch_prices()

        logger.info("Analyzing portfolio...")
        recommendations = analyze_portfolio(account_info, stock_prices)

        logger.info("Sending notifications...")
        notify_channel(recommendations)

        logger.info("Workflow completed successfully!")
    except Exception as e:
        logger.error(f"An error occurred during the workflow: {e}")

if __name__ == "__main__":
    main()