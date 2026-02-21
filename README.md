# Open-Agentic-Investor

**Open-Agentic-Investor** is an OpenClaw skill designed to autonomously fetch stock prices, analyze a given portfolio, and provide buy/sell recommendations. It can optionally integrate with the Trading 212 API to execute trades directly.

## Features
- **Stock Price Fetching:** Retrieve real-time data for portfolio stocks via a financial API.
- **Portfolio Analysis:** Apply rule-based or ML-based strategies to generate actionable insights.
- **Notifications:** Send buy/sell recommendations to channels like Telegram or Slack.
- **Trade Execution:** Optionally integrate with Trading 212 to automate trading decisions.

## Folder Structure
```plaintext
open-agentic-investor/
├── docs/                     # Documentation and guidelines
├── scripts/                  # Core scripts for functionality
├── config/                   # Configuration files
├── tests/                    # Unit and integration tests
├── cron/                     # Cron jobs (if using OpenClaw scheduling)
├── LICENSE                   # License for the project
├── README.md                 # Project overview and quick start guide
├── requirements.txt          # Python dependencies
├── .gitignore                # Ignore unnecessary files
├── skill.yaml                # OpenClaw Skill descriptor file
```

## Quick Start
1. Clone this repository:
```bash
git clone <repo_url>
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up your configuration:
   - Edit `config/config.json` with your portfolio details.
   - Add your API keys to `.env`.
4. Run the skill:
```bash
python scripts/fetch_prices.py
```

## License
This project is licensed under the MIT License.