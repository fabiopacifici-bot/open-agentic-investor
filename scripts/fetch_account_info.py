from scripts.trading_212_client import Trading212Client

def fetch_account_info():
    """Fetch account balance via Trading212Client and return the parsed result.

    This function is safe to import (no side effects at import time).
    """
    client = Trading212Client()
    try:
        return client.fetch_account_balance()
    except Exception as e:
        print("Error fetching account balance:", e)
        raise


def main():
    balance = fetch_account_info()
    print("Account Balance:", balance)


if __name__ == "__main__":
    main()