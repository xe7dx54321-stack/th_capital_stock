#!/usr/bin/env python3
"""Generate a static local HTML dashboard for Phase 32 evidence review."""

from __future__ import annotations

import argparse
import html
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase32_download_repair_workbench import build_payload as build_download_repair_payload
from smr_agents import DB_PATH
from smr_evidence_review_workbench import build_workbench
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFETY_BANNER = (
    "Evidence review workbench is read-only: no promotion, no paper order, "
    "no pending creation, and no confirmed sensitive-variable upgrades."
)


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    payload = build_workbench(conn, tickers=tickers)
    repair = build_download_repair_payload(conn, tickers=tickers)
    payload["download_repair_tasks"] = repair.get("tasks") or []
    payload["summary"]["download_repair_tasks"] = (repair.get("summary") or {}).get("repair_tasks", payload["summary"].get("download_repair_tasks", 0))
    payload["generated_at"] = now_ts()
    return payload


def _e(value: Any) -> str:
    return html.escape(str(value or ""))


def _link(url: Any) -> str:
    if not url:
        return '<span class="warning">MISSING</span>'
    safe = _e(url)
    return f'<a href="{safe}" target="_blank" rel="noopener noreferrer">{safe}</a>'


def _table(title: str, items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('priority'))}</td>"
            f"<td>{_e(item.get('ticker'))}</td>"
            f"<td>{_e(item.get('variable_type') or item.get('item_type'))}</td>"
            f"<td>{_e(item.get('quality_score'))} / {_e(item.get('quality_bucket'))}</td>"
            f"<td>{_e(item.get('lifecycle_status'))}<br>{_e(item.get('review_status'))}</td>"
            f"<td>{_e(item.get('linked_variable_pack'))}<br>{_e(item.get('link_status'))}</td>"
            f"<td>{_e(item.get('quoted_span_preview'))}</td>"
            f"<td>{_link(item.get('source_url'))}</td>"
            f"<td><code>{_e(item.get('action_command_dry_run') or 'N/A')}</code></td>"
            f"<td>{_e(', '.join(item.get('blocked_actions') or []))}</td>"
            "</tr>"
        )
    return (
        f"<section><h2>{_e(title)}</h2>"
        '<table><thead><tr><th>Priority</th><th>Ticker</th><th>Variable</th><th>Quality</th>'
        '<th>Lifecycle</th><th>Link</th><th>Quoted span preview</th><th>Source</th>'
        '<th>Dry-run command</th><th>Blocked actions</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def _repair_table(tasks: list[dict[str, Any]]) -> str:
    rows = []
    for task in tasks:
        rows.append(
            "<tr>"
            f"<td>{_e(task.get('priority'))}</td>"
            f"<td>{_e(task.get('ticker'))}</td>"
            f"<td>{_e(task.get('source_id'))}</td>"
            f"<td>{_e(task.get('reason'))}</td>"
            f"<td>{_link(task.get('source_url'))}</td>"
            f"<td>{_e(task.get('recommended_action'))}</td>"
            f"<td>{_e(task.get('notes'))}</td>"
            f"<td><code>python 08_scripts/jobs/upsert_download_unavailable_repair_tasks.py --dry-run --json</code></td>"
            "</tr>"
        )
    return (
        "<section><h2>Download Repair Task Table</h2>"
        "<table><thead><tr><th>Priority</th><th>Ticker</th><th>Source</th><th>Reason</th>"
        "<th>URL</th><th>Recommended Action</th><th>Notes</th><th>Dry-run command</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def render_html(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    items = payload.get("items") or []
    high = [item for item in items if item.get("priority") == "high"]
    sensitive = [item for item in items if item.get("sensitive_variable")]
    review_required = [item for item in items if item.get("review_status") == "review_required"]
    download = payload.get("download_repair_tasks") or []
    tickers = sorted({str(item.get("ticker")) for item in items if item.get("ticker")})
    priorities = sorted({str(item.get("priority")) for item in items if item.get("priority")})
    variables = sorted({str(item.get("variable_type")) for item in items if item.get("variable_type")})
    data_json = html.escape(json.dumps(items, ensure_ascii=False, default=str))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 32 Evidence Review Workbench</title>
  <style>
    :root {{
      --bg: #f6f1e8;
      --ink: #1f2a24;
      --muted: #687069;
      --card: #fffaf1;
      --line: #ddceb9;
      --accent: #0d6b5f;
      --warn: #a94423;
    }}
    body {{ margin: 0; background: radial-gradient(circle at top left, #dfeee5, var(--bg) 42%); color: var(--ink); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 36px 44px 20px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: -0.02em; }}
    h2 {{ margin: 28px 0 12px; }}
    .banner {{ margin: 18px 44px; padding: 16px 18px; border-left: 6px solid var(--accent); background: #eaf5ed; font-weight: 700; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; padding: 0 44px 18px; }}
    .metric {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px; box-shadow: 0 8px 24px rgba(40, 30, 20, 0.06); }}
    .metric b {{ display: block; font-size: 24px; color: var(--accent); }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 10px; padding: 0 44px 18px; }}
    select, label {{ font: inherit; }}
    select {{ padding: 8px; border: 1px solid var(--line); border-radius: 10px; background: white; }}
    section {{ padding: 0 44px 28px; }}
    table {{ width: 100%; border-collapse: collapse; background: rgba(255, 250, 241, 0.88); border: 1px solid var(--line); }}
    th, td {{ vertical-align: top; text-align: left; border-bottom: 1px solid var(--line); padding: 10px; font-size: 14px; }}
    th {{ color: var(--muted); background: #f0e5d3; }}
    code {{ white-space: pre-wrap; word-break: break-word; font-family: "Cascadia Mono", Consolas, monospace; font-size: 12px; }}
    a {{ color: var(--accent); }}
    .warning {{ color: var(--warn); font-weight: 700; }}
    .note {{ color: var(--muted); padding: 0 44px 24px; }}
  </style>
</head>
<body>
  <header>
    <h1>Phase 32 Evidence Review Workbench</h1>
    <p>Generated at {_e(payload.get('generated_at'))}. Static local dashboard; actions are shown only as dry-run commands.</p>
  </header>
  <div class="banner">{_e(SAFETY_BANNER)}</div>
  <div class="summary">
    <div class="metric"><b>{_e(summary.get('total_workbench_items'))}</b>Total items</div>
    <div class="metric"><b>{_e(summary.get('high_priority'))}</b>High priority</div>
    <div class="metric"><b>{_e(summary.get('sensitive_variable_items'))}</b>Sensitive variables</div>
    <div class="metric"><b>{_e(summary.get('review_required'))}</b>Review required</div>
    <div class="metric"><b>{_e(summary.get('download_repair_tasks'))}</b>Download repairs</div>
    <div class="metric"><b>{_e(summary.get('promotion_allowed_true'))}</b>Promotion allowed true</div>
  </div>
  <div class="filters">
    <select id="tickerFilter"><option value="">All tickers</option>{''.join(f'<option>{_e(t)}</option>' for t in tickers)}</select>
    <select id="priorityFilter"><option value="">All priorities</option>{''.join(f'<option>{_e(p)}</option>' for p in priorities)}</select>
    <select id="variableFilter"><option value="">All variables</option>{''.join(f'<option>{_e(v)}</option>' for v in variables)}</select>
    <label><input type="checkbox" id="sensitiveFilter"> Sensitive only</label>
  </div>
  <p class="note">Filters are visual helpers only. This page does not execute actions and does not contain raw document text.</p>
  {_table('High Priority Items', high)}
  {_table('Sensitive Variable Items', sensitive)}
  {_table('Review Required Items', review_required)}
  {_repair_table(download)}
  <script type="application/json" id="workbench-data">{data_json}</script>
</body>
</html>
"""


def write_html(payload: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(payload), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 32 static evidence review HTML dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    path = write_html(payload, args.output)
    print(json.dumps({"output": str(path), "summary": payload.get("summary"), "safety": payload.get("safety")}, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
