# Centralize Authentication for Open-Agentic-Investor Repository

## Goal
Create a unified, reusable authentication module to manage all API configurations and tokens across scripts. This will:
- Ensure consistent authentication.
- Prevent repeated hardcoding of credentials.
- Reduce `401 Unauthorized` errors due to mismatches.

## Current Issues
- Scripts (`fetch_prices.py`, `portfolio_manager.py`, `notifier.py`, etc.) independently manage authentication, duplicating token extraction logic.
- Errors like `401 Unauthorized` indicate potential inconsistencies in token usage due to separate implementations.

## Proposed Solution
1. **Create an Authentication Module**
    - Develop a `utils/authentication.py` to handle environment variable loading and token validation.
    - Centralize the extraction of `API_BASE_URL`, `API_KEY`, `API_SECRET`, and other shared configurations.
    - Implement a token validation function to check authentication prior to API calls.

2. **Refactor Scripts**
    - Replace individual token/loading logic in scripts (e.g., `trading_212_client.py`) with calls to `utils/authentication.py`.
    - Update existing clients (e.g., `Trading212Client`) to use the centralized module for tokens.

3. **Test Authentication**
    - Create unit tests for the `utils/authentication.py` module to ensure it:
        - Loads credentials correctly from `.env`.
        - Raises descriptive errors for missing or invalid credentials.
        - Successfully validates tokens before API interactions.

## Implementation Steps
### 1. Develop the Authentication Module
- **Path:** `utils/authentication.py`
- Functions:
    ```python
    def load_credentials():
        """
        Loads API_BASE_URL, API_KEY, API_SECRET from environment variables.
        """

    def validate_token(api_key, api_secret):
        """
        Attempts a lightweight API call to validate the provided credentials before usage.
        """
    ```

### 2. Refactor Existing Scripts
#### `trading_212_client.py`
- Replace:
    ```python
    self.api_key = os.getenv("API_KEY")
    self.api_secret = os.getenv("API_SECRET")
    ```
  - With:
    ```python
    from utils.authentication import load_credentials
    creds = load_credentials()
    self.api_key, self.api_secret = creds["api_key"], creds["api_secret"]
    ```

#### Other Scripts (`fetch_prices.py`, `notifier.py`, etc.)
- Use `authentication.load_credentials` for environment variable management.

### 3. Test New Authentication Workflow
- Unit tests should:
  - Verify credential loading under different `.env` setups.
  - Simulate invalid or missing tokens and ensure proper errors are raised.
  - Test token validation with actual API calls.

## Expected Outcome
- Uniform credential and token handling eliminates redundant code.
- Simplified maintenance for API-related changes.
- Reduced authentication errors (e.g., `401 Unauthorized`).
- Improved clarity of API interactions and reduced debugging time.

## Next Steps
Once the plan is approved:
1. Implement the `utils/authentication.py` module.
2. Refactor all dependent scripts.
3. Conduct thorough tests and validate across use cases.