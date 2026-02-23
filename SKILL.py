import argparse
from scripts.main import main as full_workflow
from scripts.fetch_account_info import fetch_account_info
from scripts.fetch_prices import fetch_prices
from scripts.portfolio_manager import analyze_portfolio
from scripts.notifier import notify_channel

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch data from APIs")
    parser.add_argument("--analyze", action="store_true", help="Analyze portfolio data")
    parser.add_argument("--notify", action="store_true", help="Send notifications")

    args = parser.parse_args()

    if args.fetch:
        fetch_account_info()
        fetch_prices()
    if args.analyze:
        analyze_portfolio()
    if args.notify:
        notify_channel("Portfolio analyzed successfully")

    if not any(vars(args).values()):
        full_workflow()