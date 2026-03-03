# Open-Agentic-Investor

**Open-Agentic-Investor** is an OpenClaw skill designed to autonomously fetch stock prices, analyze a given portfolio, and provide buy/sell recommendations. It can optionally integrate with the Trading 212 API to execute trades directly.

## Requirements

### Runtime
- Python 3.10+
- pip

### Dependencies (install via `pip install -r requirements.txt`)
- `requests` — HTTP calls to Trading 212 & Alpha Vantage APIs
- `schedule` — cron-style job scheduling
- `python-dotenv` — loads credentials from `.env`

### Environment Variables
Copy `.env.example` to `.env` and fill in your values. Never commit `.env`.

| Variable              | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| `API_KEY`             | Trading 212 API key (from Trading 212 settings > API)              |
| `API_BASE_URL`        | `https://live.trading212.com/api/v0` or demo equivalent            |
| `TELEGRAM_BOT_TOKEN`  | Telegram bot token from @BotFather                                 |
| `TELEGRAM_CHAT_ID`    | Your Telegram chat/channel ID                                      |
| `ALPHA_API`           | (Optional) Alpha Vantage API key for historical data               |

## Features
- **Stock Price Fetching:** Retrieve real-time data for portfolio stocks via a financial API.
- **Portfolio Analysis:** Apply rule-based or ML-based strategies to generate actionable insights.
- **Notifications:** Send buy/sell recommendations to channels like Telegram or Slack.
- **Trade Execution:** Optionally integrate with Trading 212 to automate trading decisions.

## Installation via OpenClaw Hub
1. Install the skill directly from OpenClaw Hub:
```bash
clawhub install open-agentic-investor
```
2. Confirm installation and dependencies setup.
3. Follow the Agent’s interactive prompts to:
   - Set up `api_keys`.
   - Validate connectivity with Trading 212 (if applicable).

## Manual Installation
1. Clone this repository (for development purposes):
```bash
git clone <repo_url>
```
2. Install Python dependencies manually:
```bash
pip install -r requirements.txt
```
3. Set up your configuration:
   - Edit `config/config.json` with your portfolio details.
   - Add your API keys to `.env`.

## Quick Start (Manual Usage)
1. Run the portfolio analysis script:
```bash
python scripts/portfolio_manager.py --action analyze-portfolio
```
2. Review buy/sell recommendations generated.

---

_Ensure compatibility with OpenClaw-specific workflows for seamless integration._