# CRON.md

## Weekly Portfolio Report

- **Task:** Generate and send a detailed portfolio analysis.
- **Frequency:** Weekly every Monday at 9:00 AM.
- **Command:**
  ```bash
  0 9 * * 1 cd /path/to/repository && python3 SKILL.py --analyze
  ```
- **Actions:**
  1. Analyze portfolio data.
  2. Send analysis report via notification to the user.