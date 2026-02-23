# Ensure a Consistent Execution Flow for Open-Agentic-Investor Repository

## Goal
Define a structured execution flow to maintain consistency across all scripts. This will:
- Synchronize script dependencies (e.g., data from one feeding into others).
- Minimize redundant processing.
- Provide a clear workflow for end-to-end operation of the skill.

## Current Issues
- Scripts are independently executed without a clearly defined sequence.
- Manual intervention is often required (e.g., entering tickers in `place_order.py`).
- Dependencies between scripts (e.g., `fetch_prices.py` and `portfolio_manager.py`) are not automated.

## Proposed Solution
1. **Entry Point Script:** Create a master script to coordinate sequential script execution and pass data between them.
    - Example flow:
      1. Fetch portfolio data using `fetch_account_info.py`.
      2. Collect stock price data with `fetch_prices.py`.
      3. Analyze stock portfolio using `portfolio_manager.py`.
      4. Notify user of recommendations using `notifier.py`.

2. **Define Input/Output Standards:**
    - Establish a consistent format for data exchanged between scripts, e.g., JSON files or Python dictionaries.
    - Shared intermediate files (e.g., `portfolio.json`) for modular reuse.

3. **Automate the Workflow:**
    - Automate user prompts (e.g., replace the `input()` in `place_order.py` with pre-configured parameters or script invocation arguments).

## Implementation Steps
### 1. Create an Entry Point Script
- **Path:** `scripts/main.py`
- **Functionality:**
  - Manages execution of all sub-scripts with robust error handling.
  - Loads .env and shared configurations.
  - Ensures sequential execution and passes data as needed.
- **Example:**
    ```python
    from fetch_account_info import fetch_account_info
    from fetch_prices import fetch_prices
    from portfolio_manager import analyze_portfolio
    from notifier import notify_channel

    def main():
        account_info = fetch_account_info()
        stock_prices = fetch_prices()
        recommendations = analyze_portfolio(account_info, stock_prices)
        notify_channel(recommendations)

    if __name__ == "__main__":
        main()
    ```

### 2. Standardize Input/Output Data
- Use JSON files as intermediaries for storing script outputs.
- Example standard:
    - **`portfolio.json`**:
      ```json
      {
        "stocks": [
          {"symbol": "AAPL", "price": 150.0, "action": "BUY"},
          {"symbol": "TSLA", "price": 720.0, "action": "SELL"}
        ]
      }
      ```

### 3. Refactor Existing Scripts
- Update scripts to:
  - Accept standardized input arguments/files.
  - Write outputs in the defined format.
- Example changes for `place_order.py`:
    - Replace user prompts (`input()` calls) with parameters.
    - Use JSON input/output for modular integration.

### 4. Test the Workflow
- Create test data for each stage:
    - Mock account info and stock price data.
    - Test data passing between scripts with controlled inputs.
- Validate that errors in one script are handled gracefully (e.g., log the issue and skip to the next step).

## Expected Outcome
- A well-defined workflow for end-to-end skill execution.
- Automated data handling between scripts eliminates the need for manual intervention and reduces redundancy.
- Simplified debugging and maintenance due to standardized input/output formats.

## Next Steps
Once the plan is approved:
1. Implement `scripts/main.py` as the entry point.
2. Standardize input/output for all scripts.
3. Test the entire workflow both incrementally and end-to-end.