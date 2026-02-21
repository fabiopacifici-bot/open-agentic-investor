from trading_212_client import Trading212Client

def main():
    client = Trading212Client()

    ticker = input("Enter the ticker (e.g., AAPL): ")
    quantity = float(input("Enter the quantity: "))
    action = input("Enter action (BUY/SELL): ")

    try:
        response = client.place_order(ticker=ticker, quantity=quantity, action=action)
        print("Order Response:", response)
    except Exception as e:
        print("Error placing order:", e)

if __name__ == "__main__":
    main()