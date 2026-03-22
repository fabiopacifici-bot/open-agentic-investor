Alpha Vantage Historical + Daily Update Implementation Plan

Goal
- Preserve existing behaviour (do not change runtime code now).
- Add a detailed, step-by-step implementation plan placed in the repository so developers can implement a robust, rate-limit-friendly flow for populating and maintaining historical price data.

High-level design
1) One-time initial full-history sync per ticker (outputsize=full) to fill price_history with complete history.
2) Regular daily incremental updates: fetch only the newest data (compact or daily latest) and insert missing rows.
3) Respect Alpha Vantage rate limits: per-request delays, exponential backoff on "Note" responses, and a configurable per-run ticker cap.
4) Metadata and orchestration: add a metadata table that tracks per-ticker sync state and last_successful_fetch timestamp to stagger and prioritise fetches.
5) Monitoring: add logging/metrics to track failures and rate-limited responses.

Files to add/modify (patch plan, not code changes now)
- scripts/fetch_daily_history.py (modify) → add incremental mode, backoff, per-run cap, env flags
- scripts/fetch_full_history.py (new) → one-shot initial full sync using outputsize=full
- scripts/fetch_alpha_snapshots.py (review) → ensure it uses new incremental flow
- scripts/cron_jobs or README updates → document how to run initial sync safely
- migrations/sql (new) → SQL or script to add metadata table to DB
- PLANS/alpha_vantage_implementation_plan.md (this file) — add detailed steps

Detailed step-by-step implementation plan

Preparation
1. Create a branch: git checkout -b feature/alpha-vantage-history

2. Add a small SQL migration script at scripts/migrations/2026-03-22__alpha_vantage_metadata.sql with contents:
   -- migration: add alphavantage metadata
   CREATE TABLE IF NOT EXISTS alpha_sync (
     ticker TEXT PRIMARY KEY,
     initial_synced INTEGER DEFAULT 0, -- 0/1
     last_success TIMESTAMP,           -- UTC time of last successful fetch
     failure_count INTEGER DEFAULT 0
   );

3. Add to repository README or TRADER.md a note about ALPHA_API usage and limits.

Implement initial full-history fetch (one-shot)
1. Add new script: scripts/fetch_full_history.py
   - Purpose: for each ticker, call Alpha Vantage with outputsize=full once and insert into price_history.
   - Safety features:
     - Read ALPHA_API from env and fail fast if not present.
     - Accept a --tickers-file or --tickers comma list so runs can be batched.
     - Accept --concurrency=1 (default) and --delay-seconds (default 1.5) between requests.
     - Before fetching a ticker, check alpha_sync.initial_synced; skip if set.
     - After successful insert (rows > 0), set initial_synced=1 and update last_success.
     - On failure, increase failure_count and continue (don’t abort full run).
     - Provide a dry-run flag to estimate total API calls/time.
   - Logging: write per-ticker logs and a summary file in /home/.../.openclaw/.alpha_full_sync_summary

2. Usage guidance (in PLANS and README):
   - Run at off-peak hours (UTC night) and/or with paid Alpha Vantage key.
   - Recommended batching: 10–20 tickers per run if using free key; add delays as needed.

Implement daily incremental fetch (production)
1. Modify scripts/fetch_daily_history.py (or create scripts/fetch_daily_incremental.py):
   - Behaviour:
     - Read env var DAILY_TICKER_CAP (default 20) — number of tickers to fetch per run.
     - Read env var ALPHA_DELAY_SECONDS (default 1.2) — delay between requests.
     - Read env var ALPHA_MAX_RETRIES (default 3) and ALPHA_BACKOFF_BASE (default 2s).
     - Use alpha_sync table to prioritise tickers not initial_synced or those with oldest last_success.
     - For each ticker selected:
       - If today’s row exists in price_history, skip.
       - Call TIME_SERIES_DAILY with outputsize=compact.
       - If response contains Note/Information (rate limit), apply backoff: sleep backoff_seconds and retry up to ALPHA_MAX_RETRIES, then mark failure_count++ and continue.
       - Insert new rows returned (INSERT OR IGNORE into price_history).
       - Update alpha_sync.last_success and reset failure_count.
   - Add instrumentation: counters for successful fetches, rate_limit_hits, failures; emit a small run summary in logs.

2. Integrate with snapshot flow:
   - The main snapshot script should call the incremental fetch as a pre-step, but respect DAILY_TICKER_CAP. This prevents snapshot runs from exhausting daily credits.

Metadata & scheduling
1. alpha_sync table design (as above) lets us stagger tickers across days. Example policy:
   - For N tickers and cap C per day, pick the C tickers with initial_synced=0 or with the oldest last_success.
   - Optionally, add weights: high-priority tickers (your portfolio top holdings) get daily refresh; low-priority get every 3–7 days.

2. Cron / Heartbeat integration:
   - Use existing heartbeat schedule (every 15 minutes) to run snapshots; but only run fetch_daily_incremental on the main hourly/6-hourly job, not every 15-min snapshot.
   - Add a separate cron: run fetch_daily_incremental once per hour (configurable); env DAILY_TICKER_CAP controls daily volume.

Rate limiting and backoff specifics
- Default: ALPHA_DELAY_SECONDS=1.2 (safe per-second spacing).
- On 'Note' response (rate limit): retry with exponential backoff: sleep = ALPHA_BACKOFF_BASE * (2 ** retry_count) seconds.
- Retry up to ALPHA_MAX_RETRIES (3). If still failing, log and increment failure_count in alpha_sync.
- If failure_count exceeds a threshold (e.g., 5) mark the ticker as backoff-suspended and skip it for 24 hours.

Testing plan
1. Unit tests: add tests/test_fetch_daily_history.py to assert behaviour for mocked successful response, Note response, incomplete data, and db insert semantics.
2. Integration test: run fetch_full_history for one ticker with a valid key and confirm price_history receives >100 rows and alpha_sync.initial_synced set.
3. Load test: simulate running across 40 tickers with delays and count total requests/time — estimate daily capacity.

Migration & Rollout plan
1. Add migration script to repo and run it in production environment (apply once): psql/sqlite execution instructions in README.
2. Run fetch_full_history in batches: start with 5–10 tickers to validate, then scale up.
3. After full sync completed for all desired tickers, enable fetch_daily_incremental in snapshot flow and disable previous aggressive per-snapshot calls (if any).
4. Monitor logs for rate-limit hits; adjust DAILY_TICKER_CAP / delays or obtain paid key.

Operational notes
- If you have many tickers (>100) consider paying for Alpha Vantage or bulk historical download from another vendor.
- Keep ALPHA_API in .env but do not commit keys to git. Use secrets manager if available.
- Add a CLI flag to force re-sync of a ticker (useful for repairing corrupted rows).

Files to create (paths)
- scripts/migrations/2026-03-22__alpha_vantage_metadata.sql
- scripts/fetch_full_history.py
- scripts/fetch_daily_incremental.py (or modify existing fetch_daily_history.py accordingly)
- PLANS/alpha_vantage_implementation_plan.md (this file)
- tests/test_fetch_daily_history.py (unit tests)

Estimated effort
- Developer time: 1–2 days for a robust implementation + tests (rate-limit/backoff, metadata, migration).
- Extra time if switching providers or purchasing a paid key.

If you'd like, I can now create the migration file and the PLANS file in the repo (no runtime code changes).