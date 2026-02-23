# Automation Plan: Open-Agentic-Investor Skill with Cron and Heartbeats

## Goal
Enhance the Open-Agentic-Investor skill by integrating periodic automation tasks using **cron** jobs and **heartbeats**:
1. Heartbeat for routine awareness tasks.
2. Cron for fixed, scheduled actions.

## Proposed Automation
### 1. **Heartbeat for Stock & Notification Monitoring**
- **Purpose:** Periodic checks (e.g., stock price alerts or notifications).
- **Behavior:**
  - Run in the main session.
  - Check stock alerts or urgent price changes every 30 minutes.
  - Notify the user if thresholds are breached or events need attention.

### 2. **Cron for Weekly Portfolio Reports**
- **Purpose:** Scheduled delivery of in-depth portfolio reports.
- **Behavior:**
  - Generate a full portfolio analysis.
  - Send it via notification at a fixed time (e.g., 9 AM every Monday).

## Implementation Details
### 1. **Heartbeat Configuration**
- Define tasks in `HEARTBEAT.md`:
  ```markdown
  # HEARTBEAT.md

  ## Periodic Monitoring
  - Monitor stock prices and alerts every 30 min.
  ```
- Implement the routine logic in `scripts/main.py` or directly within the skill’s execution flow.

### 2. **Cron Configuration**
- Create a cron job for weekly reports:
  - Command: `python3 SKILL.py --analyze`
  - Time: Every Monday at 9 AM.
- Add to system cron using:
  ```bash
  crontab -e
  ```
- Example cron entry:
  ```bash
  0 9 * * 1 cd /path/to/repository && python3 SKILL.py --analyze
  ```

## Expected Outcome
1. **Heartbeat:** Efficient periodic checks notify the user of urgent portfolio updates.
2. **Cron:** Weekly comprehensive reports keep the user engaged and informed.

## Next Steps
Once the plan is approved:
1. Implement the heartbeat logic.
2. Configure the cron job.
3. Test both mechanisms to ensure smooth operation.
4. Verify that notifications work as intended and that users receive accurate and timely updates.