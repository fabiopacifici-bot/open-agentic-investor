"""
report_export.py — Generate a self-contained mobile-friendly HTML report from SQLite data.

Run: python -m scripts.report_export (from repo root)
Output: ~/Documents/Investments/report_<timestamp>.html
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

from credential_handler import load_environment as load_credentials
from utils.logger import logger

DATA_DIR = Path(os.environ.get("INVESTMENTS_DIR", os.path.expanduser("~/Documents/Investments")))
# Override with INVESTMENTS_DIR env var
DB_PATH = DATA_DIR / "portfolio.db"


def load_data():
    if not DB_PATH.exists():
        logger.warning(f"No DB found at {DB_PATH}. Run snapshot.py first.")
        return None, [], {}, []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    snapshot = conn.execute(
        "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()

    positions = []
    recs = {}
    if snapshot:
        positions = conn.execute(
            "SELECT * FROM positions WHERE snapshot_id=?", (snapshot["id"],)
        ).fetchall()
        # Only include recommendations that belong to the latest snapshot timestamp
        # Prefer recommendations tied to the latest snapshot_id (newer schema). Fall back to timestamp if missing.
        recent_recs = []
        if snapshot and snapshot["id"]:
            recent_recs = conn.execute(
                "SELECT ticker, action, reason, price FROM recommendations WHERE snapshot_id = ? ORDER BY id DESC",
                (snapshot["id"],)
            ).fetchall()

        if not recent_recs:
            # Backward-compatible: try matching by timestamp
            recent_recs = conn.execute(
                "SELECT ticker, action, reason, price FROM recommendations WHERE timestamp = ? ORDER BY id DESC",
                (snapshot["timestamp"],)
            ).fetchall()

        # If still empty, fall back to the most recent per-ticker
        if not recent_recs:
            recent_recs = conn.execute(
                "SELECT ticker, action, reason, price FROM recommendations ORDER BY id DESC LIMIT 50"
            ).fetchall()

        for r in recent_recs:
            if r["ticker"] not in recs:
                recs[r["ticker"]] = {"action": r["action"], "reason": r["reason"], "price": r["price"]}

    # P&L history for chart (last 30 snapshots)
    history = conn.execute(
        "SELECT timestamp, total_value, pnl, pnl_pct FROM snapshots ORDER BY id DESC LIMIT 200"
    ).fetchall()
    history = list(reversed(history))

    conn.close()
    return snapshot, positions, recs, history


def generate_html(snapshot, positions, recs, history):
    if snapshot is None:
        total_value = cash = invested = pnl = pnl_pct = 0.0
        ts = "N/A"
    else:
        total_value = snapshot["total_value"] or 0.0
        cash = snapshot["cash"] or 0.0
        invested = snapshot["invested"] or 0.0
        pnl = snapshot["pnl"] or 0.0
        pnl_pct = snapshot["pnl_pct"] or 0.0
        ts = snapshot["timestamp"]

    pnl_color = "#4ade80" if pnl >= 0 else "#f87171"

    # Chart data
    chart_labels = json.dumps([r["timestamp"][:10] for r in history])
    chart_pnl = json.dumps([round(r["pnl"] or 0, 2) for r in history])
    chart_total = json.dumps([round(r["total_value"] or 0, 2) for r in history])

    # Position cards HTML
    position_cards = ""
    for p in positions:
        ticker = p["ticker"] or ""
        value = p["value"] or 0.0
        pos_pnl = p["pnl"] or 0.0
        pos_pnl_pct = p["pnl_pct"] or 0.0
        rec = recs.get(ticker, {})
        action = rec.get("action", "HOLD")
        badge_color = {"BUY": "#4ade80", "SELL": "#f87171"}.get(action, "#facc15")
        pnl_c = "#4ade80" if pos_pnl >= 0 else "#f87171"
        position_cards += f"""
        <div class="card position-card">
          <div class="pos-header">
            <span class="ticker">{ticker}</span>
            <span class="badge" style="background:{badge_color};color:#111">{action}</span>
          </div>
          <div class="pos-details">
            <span>Value: <b>${value:.2f}</b></span>
            <span style="color:{pnl_c}">P&amp;L: {pos_pnl_pct:+.2f}%</span>
          </div>
          <div class="pos-reason">{rec.get('reason','')}</div>
        </div>"""

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Portfolio Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0f172a; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 16px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  .subtitle {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
  .summary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .metric {{ }}
  .metric-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
  .metric-value {{ font-size: 1.5rem; font-weight: 700; }}
  .section-title {{ font-size: 1rem; font-weight: 600; margin-bottom: 12px; color: #cbd5e1; }}
  .tabs {{ display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }}
  .tab {{ padding: 4px 12px; border-radius: 20px; border: 1px solid #334155; background: transparent; color: #94a3b8; cursor: pointer; font-size: 0.8rem; }}
  .tab.active {{ background: #3b82f6; border-color: #3b82f6; color: white; }}
  .position-card {{ padding: 12px 16px; }}
  .pos-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
  .ticker {{ font-weight: 700; font-size: 1rem; }}
  .badge {{ padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }}
  .pos-details {{ display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px; }}
  .pos-reason {{ font-size: 0.75rem; color: #64748b; }}
  canvas {{ max-height: 220px; }}
  @media (max-width: 400px) {{ .summary-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<h1>📈 Portfolio Report</h1>
<p class="subtitle">Generated {generated_at} · Data as of {ts[:16] if ts != 'N/A' else 'N/A'}</p>

<div class="card">
  <div class="section-title">Portfolio Summary</div>
  <div class="summary-grid">
    <div class="metric">
      <div class="metric-label">Total Value</div>
      <div class="metric-value">${total_value:.2f}</div>
    </div>
    <div class="metric">
      <div class="metric-label">P&amp;L</div>
      <div class="metric-value" style="color:{pnl_color}">{pnl:+.2f} ({pnl_pct:+.2f}%)</div>
    </div>
    <div class="metric">
      <div class="metric-label">Invested</div>
      <div class="metric-value">${invested:.2f}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Cash</div>
      <div class="metric-value">${cash:.2f}</div>
    </div>
  </div>
</div>

<div class="card">
  <div class="section-title">P&amp;L History</div>
  <canvas id="pnlChart"></canvas>
</div>

<div class="card">
  <div class="section-title">Portfolio Value</div>
  <canvas id="valueChart"></canvas>
</div>

<div class="section-title" style="padding: 0 4px 8px">Positions ({len(positions)})</div>
{position_cards if position_cards else '<div class="card" style="color:#64748b">No positions found. Run snapshot.py first.</div>'}

<script>
const labels = {chart_labels};
const pnlData = {chart_pnl};
const totalData = {chart_total};
const chartDefaults = {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color:'#64748b', maxTicksLimit: 6 }}, grid: {{ color:'#1e293b' }} }}, y: {{ ticks: {{ color:'#64748b' }}, grid: {{ color:'#334155' }} }} }} }};
new Chart(document.getElementById('pnlChart'), {{ type:'line', data: {{ labels, datasets: [{{ data: pnlData, borderColor:'#4ade80', backgroundColor:'rgba(74,222,128,0.1)', fill:true, tension:0.3, pointRadius:2 }}] }}, options: chartDefaults }});
new Chart(document.getElementById('valueChart'), {{ type:'line', data: {{ labels, datasets: [{{ data: totalData, borderColor:'#60a5fa', backgroundColor:'rgba(96,165,250,0.1)', fill:true, tension:0.3, pointRadius:2 }}] }}, options: chartDefaults }});
</script>
</body>
</html>"""


def run_export():
    load_credentials()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    result = load_data()
    snapshot, positions, recs, history = result

    html = generate_html(snapshot, positions, recs, history)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = DATA_DIR / f"report_{ts}.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info(f"Report saved to {out_path}")
    print(f"Report saved: {out_path}")

    # Copy to openclaw media dir for Telegram delivery
    import shutil
    media_dir = Path.home() / ".openclaw" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    media_path = media_dir / f"report_{ts}.html"
    shutil.copy2(out_path, media_path)
    print(f"Media copy: {media_path}")
    return str(media_path)


if __name__ == "__main__":
    run_export()
