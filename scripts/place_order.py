from scripts.trading_212_client import Trading212Client
from utils.logger import logger

def main():
    """Interactive order placement tool."""
    client = Trading212Client()

    try:
        ticker = input("Enter the ticker (e.g., AAPL): ").strip().upper()
        if not ticker:
            print("Error: Ticker is required")
            return
        
        quantity_str = input("Enter the quantity: ").strip()
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                print("Error: Quantity must be positive")
                return
        except ValueError:
            print("Error: Quantity must be a number")
            return
        
        action = input("Enter action (BUY/SELL): ").strip().upper()
        if action not in ["BUY", "SELL"]:
            print("Error: Action must be BUY or SELL")
            return

        # Confirm order
        print(f"\nOrder Summary:")
        print(f"  Action: {action}")
        print(f"  Ticker: {ticker}")
        print(f"  Quantity: {quantity}")
        confirm = input("\nConfirm order? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("Order cancelled.")
            return

        response = client.place_order(ticker=ticker, quantity=quantity, action=action)
        print("\n✓ Order Response:", response)
        logger.info(f"Order placed successfully: {action} {quantity} {ticker}")
        
    except Exception as e:
        error_msg = f"Error placing order: {e}"
        logger.error(error_msg)
        print(f"\n✗ {error_msg}")
        raise

if __name__ == "__main__":
    main()