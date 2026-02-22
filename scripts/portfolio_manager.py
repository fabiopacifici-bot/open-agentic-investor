from trading_212_client import Trading212Client

def list_stocks(client):
    try:
        stocks = client.fetch_positions()  # Correct method to fetch stock positions
        print("Your Stock Holdings:", stocks)
        return stocks
    except Exception as e:
        print("Error fetching stocks:", e)
        return None

def analyze_all_stocks(client):
    # Analyze portfolio for buy/sell/hold recommendations for all stocks
    timestamp = "2026-02-22"
    stocks = client.fetch_positions()

    report = []

    for stock in stocks:
        ticker = stock['instrument']['ticker']
        name = stock['instrument']['name']
        price = stock['currentPrice']
        avg_paid = stock['averagePricePaid']
        pl = stock['walletImpact']['unrealizedProfitLoss']

        action = "HOLD"
        if price < avg_paid * 0.9:  # Example: Buy if price is 10% below average paid
            action = "BUY"
        elif price > avg_paid * 1.1:  # Example: Sell if price is 10% above average paid
            action = "SELL"
        report.append({"Ticker": ticker, "Name": name, "Action": action, "Current Price": price, "Average Paid": avg_paid, "Unrealized P/L": pl})

    # Write analysis to a file
    with open(f"portfolio_report_{timestamp}.txt", "w") as f:
        f.write(f"Portfolio Analysis - {timestamp}\n\n")
        for entry in report:
            f.write(f"Ticker: {entry['Ticker']}\n")
            f.write(f"Name: {entry['Name']}\n")
            f.write(f"Current Price: {entry['Current Price']}\n")
            f.write(f"Average Paid: {entry['Average Paid']}\n")
            f.write(f"Unrealized P/L: {entry['Unrealized P/L']}\n")
            f.write(f"Action: {entry['Action']}\n\n")

if __name__ == "__main__":
    client = Trading212Client()
    analyze_all_stocks(client)