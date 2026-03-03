import argparse
from scripts.main import main as full_workflow
from scripts.fetch_account_info import fetch_account_info
from scripts.fetch_prices import fetch_stock_prices
from scripts.portfolio_manager import analyze_portfolio
from scripts.notifier import notify_channel

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Open Agentic Investor - Portfolio analysis and trading skill"
    )
    parser.add_argument("--fetch", action="store_true", help="Fetch account and price data from APIs")
    parser.add_argument("--analyze", action="store_true", help="Analyze portfolio and generate recommendations")
    parser.add_argument("--notify", action="store_true", help="Send test notification")

    args = parser.parse_args()

    if args.fetch:
        print("Fetching account information...")
        account_info = fetch_account_info()
        print(f"\u2713 Account info retrieved: {account_info}")
        
        print("\nFetching stock prices...")
        stock_prices = fetch_stock_prices()
        print(f"\u2713 Retrieved prices for {len(stock_prices)} positions")
        
    elif args.analyze:
        print("Analyzing portfolio...")
        # Fetch data first
        account_info = fetch_account_info()
        stock_prices = fetch_stock_prices()
        
        # Analyze
        recommendations = analyze_portfolio(account_info, stock_prices)
        
        if recommendations:
            print(f"\n\u2713 Generated {len(recommendations)} recommendations:")
            for rec in recommendations:
                print(f"  - {rec['action']} {rec['ticker']} at ${rec['current_price']:.2f}")
        else:
            print("\u2713 No recommendations at this time")
            
    elif args.notify:
        test_message = "Test notification from Open Agentic Investor skill"
        print("Sending test notification...")
        notify_channel(test_message)
        
    else:
        # Run full workflow if no specific action specified
        print("Running full portfolio analysis workflow...")
        full_workflow()