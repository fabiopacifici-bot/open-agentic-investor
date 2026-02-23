# Git History Security Cleanup

**Date:** February 24, 2026  
**Issue:** Hardcoded credentials found in git history  
**Status:** In Progress  

## Problem

Commit `fa5887d` ("Add dynamic credential handling for API_KEY and API_SECRET with fallback to .env") contains hardcoded Telegram credentials in `scripts/OpenClaw.py`:

```python
TELEGRAM_BOT_TOKEN: "8502164226:AAH1xTbtzPI5T-Hqbbr2Jd7vRljer_KddyA"
TELEGRAM_CHAT_ID: "6395145098"
```

**Critical:** These commits have NOT been pushed to remote yet, so we can safely rewrite history.

## Affected Commits

- `fa5887d` - Contains the hardcoded credentials in scripts/OpenClaw.py

## Commits Ahead of Remote (Not Pushed)

All these commits are local only:
```
75f36ff (HEAD -> issue-6) Add integration plan and enhance documentation for Alpha Vantage API usage
d4cd27a Add validation output log for historical data scripts
4710b91 (dev) refactoring updates
c246e49 Ensure dotenv is loaded in credential_handler before falling back to user input
453d757 Remove load_dotenv reference to complete dynamic credential injection
fa5887d Add dynamic credential handling for API_KEY and API_SECRET with fallback to .env ⚠️ CONTAINS SECRETS
3f1f7dd Remove FINANCIAL_API_KEY and align fetch_prices to use Trading 212 API instead of Alphavantage
ac9dbe6 Add logs/skill.log to .gitignore to keep logs untracked
7ded9b0 Add OpenClaw skill metadata improvements
```

## Solution Strategy

### Option 1: Interactive Rebase (Recommended)
Use `git rebase -i` to edit commit fa5887d and remove/replace the hardcoded credentials.

Steps:
1. Commit current fixes (they don't contain secrets)
2. `git rebase -i 1863f10` (parent of oldest unpushed commit)
3. Mark commit fa5887d for "edit"
4. Amend the commit to replace hardcoded values with env var lookups
5. Continue rebase

### Option 2: Filter-Branch (Nuclear option)
Use git filter-branch to remove the file from history entirely and re-add it clean.

### Option 3: BFG Repo-Cleaner
Use BFG tool to scrub credentials from history.

## Execution Plan

We'll use **Option 1** (Interactive Rebase) as it's cleanest and preserves commits.

1. ✓ Document current state
2. [ ] Commit current comprehensive fixes
3. [ ] Create backup branch
4. [ ] Interactive rebase to fix commit fa5887d
5. [ ] Verify credentials are removed
6. [ ] Update dev branch
7. [ ] Verify with git log and grep

## Backup Strategy

Before rewriting history:
```bash
git branch backup/before-history-cleanup
```

## Verification Commands

After cleanup:
```bash
# Search for credential patterns in entire history
git log --all --full-history -p | grep -E "(8502164226|6395145098|AAH1xTbtzPI5T)"

# Should return nothing
```

## Post-Cleanup Actions

1. Verify credentials are gone from history
2. Ensure .env.example is in place (no real credentials)
3. Document this incident
4. Update .gitignore if needed
5. Safe to push to remote after verification

## Notes

- The credentials were Telegram bot tokens, which should be rotated after this cleanup
- All fixes remove hardcoded credentials and use environment variables instead
- .env.example created with placeholder values
- Real .env file should never be committed (already in .gitignore)
