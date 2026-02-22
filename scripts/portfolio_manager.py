from trading_212_client import Trading212Client

def list_stocks(client):
    try:
        stocks = client.fetch_account_balance()  # Assuming stock fetch is similar to account
        print("Your Stock Holdings:", stocks)
        return stocks
    except Exception as e:
        print("Error fetching stocks:", e)
        return None

def analyze_portfolio():
    # Placeholder logic for portfolio analysis
    # Define your analysis conditions here (e.g., moving averages, thresholds)
    recommendations = [
        {"ticker": "AAPL", "action": "BUY", "quantity": 10},
        {"ticker": "TSLA", "action": "SELL", "quantity": 5}
    ]
    return recommendations

def main(action):
    client = Trading212Client()

    if action == "list-stocks":
        list_stocks(client)
    elif action == "analyze-portfolio":
        # Analyze portfolio and fetch recommendations
        recommendations = analyze_portfolio()

        for rec in recommendations:
            try:
                response = client.place_order(
                    ticker=rec["ticker"], 
                    quantity=rec["quantity"] if rec["action"] == "BUY" else -rec["quantity"],
                    action=rec["action"]
                )
                print(f"Order for {rec['ticker']} ({rec['action']}):", response)
            except Exception as e:
                print(f"Error placing order for {rec['ticker']}:", e)
    else:
        print("Invalid action. Available actions: list-stocks, analyze-portfolio.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Portfolio Manager")
    parser.add_argument("--action", type=str, required=True, help="Action to perform: list-stocks or analyze-portfolio")
    args = parser.parse_args()
    main(args.action)