# Diagnostic Logging for Open-Agentic-Investor Repository

## Goal
Enhance logging capabilities across scripts to improve debugging, error analysis, and execution traceability. This will:
- Provide detailed logs for all API calls, script actions, and errors.
- Enable easy identification of issues in the skill workflow.
- Support long-term maintainability and monitoring.

## Current Issues
- Limited logging in scripts makes error diagnosis difficult (e.g., unclear causes of 404 and 401 errors).
- Logs are inconsistent across modules, reducing traceability of operations.
- Logs do not differentiate between warnings, errors, and informational messages.

## Proposed Solution
1. **Standardized Logging Framework:**
    - Use Python’s built-in `logging` module to provide consistent, centralized logs across all scripts.
    - Define log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) for structured reporting.

2. **Add Contextual Logs:**
    - Include logs for:
        - API request details (endpoints, payloads, responses).
        - Script execution stages.
        - Errors and exceptions.

3. **Centralized Log File:**
    - Write all logs to a central file (e.g., `logs/skill.log`).
    - Include timestamps for each log entry.

## Implementation Steps
### 1. Define Logging Configuration
- Create a `utils/logger.py` module for reusable logging setup:
    ```python
    import logging

    LOG_FILE = "logs/skill.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("skill_logger")
    ```

### 2. Integrate Logging into Scripts
- Replace `print()` calls with `logger` log messages in all scripts.
- Example changes for `trading_212_client.py`:
    - Replace:
        ```python
        print("Request Headers:", self.auth_header)
        ```
      - With:
        ```python
        logger.debug(f"Request headers: {self.auth_header}")
        ```
    - Add logs for request endpoints and responses:
        ```python
        logger.info(f"Fetching account balance from {endpoint}")
        logger.debug(f"Response: {response.json()}")
        ```

### 3. Distinguish Log Levels
- Use appropriate log levels:
    - `DEBUG`: Detailed data (e.g., request payloads, function inputs).
    - `INFO`: High-level actions (e.g., script stages, successful API calls).
    - `WARNING`: Minor issues that do not halt execution (e.g., partial failures).
    - `ERROR`: Significant issues requiring attention.
    - `CRITICAL`: Fatal errors that terminate execution.

### 4. Test the Logging System
- Verify that logs capture sufficient detail without redundancy.
- Simulate various scenarios (e.g., invalid API tokens, missing `.env` values) to check error messages.
- Test both console and file logging.

## Expected Outcome
- Comprehensive, structured logs across all scripts.
- Centralized log file for easier monitoring and debugging.
- Improved visibility into API and skill execution flows.

## Next Steps
Once the plan is approved:
1. Implement `utils/logger.py` for logging configuration.
2. Update all scripts to use the centralized logging system.
3. Test logging under various scenarios.