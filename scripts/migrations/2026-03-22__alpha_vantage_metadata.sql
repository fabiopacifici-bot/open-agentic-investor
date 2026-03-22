-- migration: add alphavantage metadata
CREATE TABLE IF NOT EXISTS alpha_sync (
  ticker TEXT PRIMARY KEY,
  initial_synced INTEGER DEFAULT 0,
  last_success TIMESTAMP,
  failure_count INTEGER DEFAULT 0
);
