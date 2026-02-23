# Skill Configuration Improvements (Plan)

## Objective
Prepare the `open-agentic-investor` skill for seamless integration into OpenClaw, ensuring compatibility, proper configuration, and readiness for testing and deployment via ClawHub.

---

## Key Improvements

### 1. **Slash Commands Integration**
Enable `/...` commands to trigger specific workflows in the skill. Define slash commands in the skill configuration.
- **Examples to Add:**
  - `/agentic-investor fetch` → `SKILL.py --fetch`
  - `/agentic-investor analyze` → `SKILL.py --analyze`
  - `/agentic-investor notify` → `SKILL.py --notify`
- **Actions:** Ensure `SKILL.md` and potential config files override OpenClaw’s Gateway.

---

### 2. **Skill Precedence and Location**
Ensure the skill is installed correctly to prioritize OpenClaw’s workspace hierarchy.
- **Planned Actions:**
  - Verify skill resides in `<workspace>/skills/open-agentic-investor`.

---

### 3. **`SKILL.md` Optimizations**
Ensure `SKILL.md` reflects accurate metadata (name, entry points, tags, etc.):
- **Metadata:** Add keywords, detailed description, and accurate tags for discoverability.
- **Functionality Mapping:** Confirm YAML frontmatter maps inputs properly to flags.

---

### 4. **OpenClaw Skill Config**
Update the OpenClaw `openclaw.json` file with specific configurations:
- **Enable Skill:** Ensure `open-agentic-investor` is enabled in `skills.entries`:
  ```json
  "skills": {
    "entries": {
      "open-agentic-investor": {
        "enabled": true,
        "env": {
          "API_KEY": "<api-key>",
          "API_SECRET": "<api-secret>",
          "TELEGRAM_BOT_TOKEN": "<telegram-bot-token>"
        }
      }
    }
  }
  ```
- **Add Directories:** Verify it remains prioritized in `load.extraDirs`.

---

### 5. **ClawHub Compatibility**
Prepare the skill for ClawHub deployment:
- **Actions:**
  - Add versioning to `SKILL.md` (`v1.0.0`).
  - Test a `clawhub publish` workflow.
  - Add tags to improve discoverability.

---

## Next Steps
1. Address all planned improvements iteratively.
2. Verify skill functionality using `/...` slash commands and manual tests.
3. Prepare for final ClawHub integration once functionality is approved.
