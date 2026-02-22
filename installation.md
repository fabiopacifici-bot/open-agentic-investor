# Open-Agentic-Investor Skill Installation

## Key Features
- Automates investment portfolio management.
- Offers tailored buy/sell/hold recommendations based on market data and user preferences.
- Integrates risk profiling and recovery strategies.

## Installation Steps
1. Clone the `open-agentic-investor` repository into OpenClaw's skills directory.
2. Navigate to the skill directory during setup.
3. Ensure the following dependencies are installed:
   - Python 3.9+
   - Required libraries (see `requirements.txt`).

4. During installation, the skill will:
   - Prompt for API keys (e.g., Trading 212 API key and secret).
   - Populate `FINANCE.md` with workflow details (if not already present).
   - Test connectivity with provided APIs.

## Initial Configuration
The agent will guide you through setup:
- **Step 1**: Confirm portfolio data retrieval via Trading 212 API.
- **Step 2**: Provide risk preferences (conservative, moderate, or aggressive).
- **Step 3**: Validate and customize workflows, including buy/sell criteria thresholds.

---

> _This installation process ensures the Agent is fully configured to operate intelligently and dynamically._