import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from utils.logger import logger

# ─── Deduplication state ──────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parent.parent
_STATE_FILE = _REPO_ROOT / "data" / "last_notifications.json"
_CET = ZoneInfo("Europe/Berlin")

# Cooldown constants (hours)
_COOLDOWN_SIGNAL  = 4      # BUY / SELL signals
_COOLDOWN_ALERT   = 0.5    # Price spike / P&L alerts
_COOLDOWN_HEARTBEAT = 24   # Daily summary


def _load_state() -> dict:
    """Load notification state from disk."""
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if _STATE_FILE.exists():
            return json.loads(_STATE_FILE.read_text())
    except Exception as e:
        logger.warning(f"Could not load notification state: {e}")
    return {}


def _save_state(state: dict):
    """Persist notification state to disk."""
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        logger.warning(f"Could not save notification state: {e}")


def should_notify(signal_key: str, cooldown_hours: float) -> bool:
    """Return True if this signal_key hasn't been sent within cooldown_hours.

    Args:
        signal_key:      Unique identifier for the notification, e.g. "BUY_NVDA".
        cooldown_hours:  Minimum hours between sends for this key.

    Returns:
        True if the notification should be sent, False if it's still in cooldown.
    """
    state = _load_state()
    last_sent = state.get(signal_key)
    if last_sent is None:
        return True
    elapsed_hours = (time.time() - last_sent) / 3600
    return elapsed_hours >= cooldown_hours


def mark_notified(signal_key: str):
    """Record that signal_key was sent right now."""
    state = _load_state()
    state[signal_key] = time.time()
    _save_state(state)


def is_heartbeat_window() -> bool:
    """Return True only between 08:55–09:10 CET (daily summary window)."""
    now = datetime.now(_CET)
    total_min = now.hour * 60 + now.minute
    return (8 * 60 + 55) <= total_min <= (9 * 60 + 10)


# ─── Core notification ────────────────────────────────────────────────────────

def notify_channel(message, signal_key: str = None, cooldown_hours: float = None) -> bool:
    """Send notification message via Telegram with optional deduplication.

    Deduplication rules (applied when signal_key is provided or message is a list):
    - List of recommendations: each BUY/SELL is deduplicated individually
      with a 4-hour cooldown; empty list is silently dropped.
    - String with signal_key: deduped according to cooldown_hours (default 4h for
      BUY_/SELL_ keys, 0.5h for ALERT_ keys, 24h for heartbeat).
    - String without signal_key: sent unconditionally (legacy behaviour).

    Args:
        message:        Message text (str) or list of recommendation dicts.
        signal_key:     Optional dedup key, e.g. "BUY_NVDA", "ALERT_PNL", "heartbeat".
        cooldown_hours: Override cooldown; auto-detected from signal_key if omitted.

    Returns:
        bool: True if at least one notification was sent (or queued).
    """
    # Short-circuit outbound network calls when NO_OUTBOUND env var is set (used in testing/subagent runs)
    if os.getenv('NO_OUTBOUND', '').lower() in ('1','true','yes'):
        print('notify_channel: NO_OUTBOUND set — skipping network call')
        return True

    # ── List of recommendations ───────────────────────────────────────────────
    if isinstance(message, list):
        if not message:
            # Silence is fine — no "no recommendations" spam
            logger.info("notify_channel: no recommendations, skipping notification")
            return False

        sent_any = False
        for rec in message:
            action = rec.get('action', '').upper()
            ticker = rec.get('ticker', 'UNKNOWN')
            rec_key = f"{action}_{ticker}"

            # Resolve cooldown for this signal
            cd = cooldown_hours if cooldown_hours is not None else _COOLDOWN_SIGNAL

            if not should_notify(rec_key, cd):
                logger.info(f"notify_channel: skipping {rec_key} (still in {cd}h cooldown)")
                continue

            action_emoji = "🟢" if action == 'BUY' else "🔴"
            formatted = (
                f"\n📊 *Trading Signal* \n\n"
                f"{action_emoji} *{action} {ticker}*\n"
                f"   Price: ${rec.get('current_price', 0):.2f}\n"
                f"   Quantity: {rec.get('quantity', 0)}\n"
                f"   Reason: {rec.get('reason', 'N/A')}\n"
            )
            if _send_telegram(formatted):
                mark_notified(rec_key)
                sent_any = True

        return sent_any

    # ── String message ────────────────────────────────────────────────────────
    formatted_message = str(message)

    if signal_key is not None:
        # Auto-detect cooldown if not explicitly provided
        if cooldown_hours is None:
            key_upper = signal_key.upper()
            if key_upper.startswith('ALERT'):
                cooldown_hours = _COOLDOWN_ALERT
            elif key_upper in ('HEARTBEAT', 'SUMMARY', 'DAILY'):
                cooldown_hours = _COOLDOWN_HEARTBEAT
            else:
                cooldown_hours = _COOLDOWN_SIGNAL

        if not should_notify(signal_key, cooldown_hours):
            logger.info(f"notify_channel: skipping '{signal_key}' (still in {cooldown_hours}h cooldown)")
            return False

        # Heartbeat: only send inside the morning window unless explicitly forced
        if signal_key.upper() in ('HEARTBEAT', 'SUMMARY', 'DAILY') and not is_heartbeat_window():
            logger.info("notify_channel: heartbeat outside window, skipping")
            return False

    if _send_telegram(formatted_message):
        if signal_key:
            mark_notified(signal_key)
        return True
    return False


def _send_telegram(formatted_message: str) -> bool:
    """Low-level Telegram API call.  Returns True on success."""
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", None)
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", None)

    if not telegram_bot_token:
        error_msg = "Error: TELEGRAM_BOT_TOKEN environment variable is not set."
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not telegram_chat_id:
        error_msg = "Error: TELEGRAM_CHAT_ID environment variable is not set."
        logger.error(error_msg)
        raise ValueError(error_msg)

    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": formatted_message,
        "parse_mode": "Markdown"
    }

    try:
        logger.info(f"Sending notification to Telegram chat {telegram_chat_id}")
        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("Notification sent successfully")
            print("✓ Notification sent successfully")
            return True
        else:
            error_msg = f"Failed to send notification. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            print(f"✗ {error_msg}")
            response.raise_for_status()
            return False
    except requests.RequestException as e:
        error_msg = f"Network error sending notification: {e}"
        logger.error(error_msg)
        raise


def send_report_file(filepath: str, caption: str = "📊 Portfolio Report") -> bool:
    """Send an HTML report file to Telegram as a document attachment.

    Args:
        filepath: Path to the HTML file to send.
        caption: Caption text shown with the file.

    Returns:
        bool: True if sent successfully.
    """
    if os.getenv('NO_OUTBOUND', '').lower() in ('1', 'true', 'yes'):
        print(f'send_report_file: NO_OUTBOUND set — skipping network call (file: {filepath})')
        return True

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    if not telegram_chat_id:
        raise ValueError("TELEGRAM_CHAT_ID not set")

    api_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                api_url,
                data={"chat_id": telegram_chat_id, "caption": caption},
                files={"document": (os.path.basename(filepath), f, "text/html")},
                timeout=30,
            )
        if response.status_code == 200:
            logger.info(f"Report file sent: {filepath}")
            return True
        else:
            logger.error(f"Failed to send report file: {response.status_code} {response.text}")
            response.raise_for_status()
            return False
    except requests.RequestException as e:
        logger.error(f"Network error sending report file: {e}")
        raise


def main():
    """Entry point for standalone execution — no-op (dedup guards prevent test-message spam)."""
    # Previously this sent a hardcoded test message on every invocation.
    # Now it does nothing unless explicitly triggered with a real message.
    logger.info("notifier.py: main() called with no payload — nothing to send")
    print("notifier.py: run as library. Use notify_channel() directly.")


if __name__ == "__main__":
    main()
