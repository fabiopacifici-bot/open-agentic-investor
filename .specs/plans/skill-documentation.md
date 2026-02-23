# Skill Documentation & Reference Cleanup for Open-Agentic-Investor

## Goal
Refine the skill's documentation to provide clear, actionable guidance for usage, troubleshooting, and integration. This will:
- Ensure that users and agents understand the skill’s workflows and dependencies.
- Provide details about environment setup, script roles, and expected outcomes.
- Make the skill maintainable and extensible.

## Current Issues
- `SKILL.md` lacks detailed procedural guidance for using the skill end-to-end.
- The relationship between scripts and their sequence is unclear.
- Environment variable configurations and dependencies are not fully documented.

## Proposed Solution
1. **Revise `SKILL.md`:**
    - Add a high-level overview of the skill.
    - Include step-by-step instructions for using the skill.
    - Outline required environment variables and their expected values.

2. **Add Reference Documentation:**
    - Create a `references/` folder for supporting documents (e.g., API specs, workflows).
    - Provide examples of input/output data where applicable.

3. **Document the Script Workflow:**
    - Highlight how scripts interact, their sequence, and dependencies.

## Implementation Steps
### 1. Revise `SKILL.md`
- Include the following sections:
    - **Overview:**
        - A description of what the skill does (e.g., portfolio analysis, stock notifications).
    - **Prerequisites:**
        - Required tools (e.g., Python, virtualenv).
        - Setup instructions for `.env`.
    - **Usage:**
        - Step-by-step instructions to execute the skill (via `SKILL.py` or individual scripts).
    - **Examples:**
        - Illustrative examples of inputs, outputs, and results.
    - **Troubleshooting:**
        - Common issues (e.g., 401 errors, 404 errors) and their resolutions.

### 2. Create Reference Documentation
- Add files in the `references/` folder:
    - **`api_specifications.md`:** Overview of API endpoints used (e.g., `/equity/account/cash`, `/equity/order`).
    - **`example_inputs_outputs.md`:** Examples of input data (e.g., JSON objects) and expected outputs.
    - **`environment_variables.md`:** Details of required `.env` variables:
        ```plaintext
        API_BASE_URL - The base URL for Trading 212 API.
        API_KEY - The API key for authentication.
        API_SECRET - The API secret for authentication.
        TELEGRAM_BOT_TOKEN - Token for sending Telegram notifications.
        TELEGRAM_CHAT_ID - Chat ID for Telegram notifications.
        ```

### 3. Document the Script Workflow
- Add a section in `SKILL.md`:
    - **Script Overview:**
        - Explain the role of each script.
        - Example:
            ```
            - `fetch_prices.py`: Retrieves real-time stock prices.
            - `portfolio_manager.py`: Analyzes the stock portfolio and provides buy/sell recommendations.
            - `notifier.py`: Sends notifications with analysis results to Telegram.
            ```
    - **Script Sequence:**
        - Diagram or list the workflow:
            ```plaintext
            1. Fetch portfolio data (`fetch_account_info.py`).
            2. Fetch stock prices (`fetch_prices.py`).
            3. Analyze portfolio (`portfolio_manager.py`).
            4. Notify user (`notifier.py`).
            ```

### 4. Add Maintenance Notes
- Provide guidelines for modifying the skill:
    - How to update API endpoints if they change.
    - How to add new scripts or extend functionality.

## Expected Outcome
- Clear, actionable documentation for users and agents.
- Comprehensive references for APIs, inputs/outputs, and environment setup.
- Detailed workflow instructions to simplify skill integration and use.

## Next Steps
Once the plan is approved:
1. Revise `SKILL.md` with the proposed sections.
2. Create detailed reference documents.
3. Test the documentation by running the skill as instructed, refining as needed.