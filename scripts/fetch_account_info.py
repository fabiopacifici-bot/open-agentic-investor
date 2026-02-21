from trading_212_client import Trading212Client

def main():
    client = Trading212Client()
    
    try:
        balance = client.fetch_account_balance()
        print("Account Balance:", balance)
    except Exception as e:
        print("Error fetching account balance:", e)

if __name__ == "__main__":
    main()