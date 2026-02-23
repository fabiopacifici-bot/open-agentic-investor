# CRON.md

## Weekly Portfolio Report (Gateway Cron)

- **Task:** Generate a detailed portfolio report and send as notification.
- **Frequency:** Weekly every Monday at 9:00 AM.
- **Configuration:**
  - Command: `cron.schedule`
  - Example:
    ```bash
    {
      "name": "weekly-portfolio-report",
      "schedule": "0 9 * * 1",
      "task": "python3 SKILL.py --analyze",
      "mode": "isolated",
      "delivery": {
        "mode": "chat"
      }
    }
    ```
- **Actions:**
  1. Schedule the job using the above configuration.
  2. Ensure the Gateway wakes and delivers the report efficiently.