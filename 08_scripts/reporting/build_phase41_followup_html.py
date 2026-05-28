#!/usr/bin/env python3
"""Generate a static read-only Phase 41 follow-up HTML page."""

from __future__ import annotations

import argparse
import html
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_customer_allocation_route import build_payload as build_customer_allocation
from build_phase41_followup_dashboard import build_payload as build_dashboard
from build_phase41_followup_trigger_summary import build_payload as build_trigger
from build_phase41_official_consensus_availability import build_payload as build_official_consensus
from build_phase41_research_followup_queue import build_payload as build_queue
from build_phase41_supplier_share_route import build_payload as build_supplier_share
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFETY_BANNER = (
    "Phase 41 follow-up page is read-only: it does not fetch sources, write evidence, "
    "create pending review, create paper orders, relax promotion, or trade."
)


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    ticker = "300308.SZ"
    return {
        "generated_at": now_ts(),
        "trigger": build_trigger(conn, ticker),
        "queue": build_queue(conn, ticker),
        "official_consensus": build_official_consensus(conn, ticker),
        "supplier_share": build_supplier_share(conn, ticker),
        "customer_allocation": build_customer_allocation(conn, ticker),
        "dashboard": build_dashboard(conn),
        "safety": {
            "html_is_read_only": True,
            "action_execution_enabled": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def _item_rows(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('followup_item_id'))}</td>"
            f"<td>{_e(item.get('item_type'))}</td>"
            f"<td>{_e(item.get('priority'))}</td>"
            f"<td>{_e(item.get('route_status'))}</td>"
            f"<td>{_e(item.get('allowed_usage_target'))}</td>"
            f"<td>{_e('; '.join(item.get('do_not_do') or []))}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_html(payload: dict[str, Any]) -> str:
    queue = payload.get("queue") or {}
    dashboard = payload.get("dashboard") or {}
    official = ((payload.get("official_consensus") or {}).get("official_consensus_availability") or {})
    supplier = ((payload.get("supplier_share") or {}).get("supplier_share_route") or {})
    customer = ((payload.get("customer_allocation") or {}).get("customer_allocation_route") or {})
    summary = dashboard.get("summary") or {}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 41 Research Follow-up Queue</title>
  <style>
    :root {{
      --bg: #f4efe3;
      --ink: #1f2926;
      --card: #fffaf0;
      --line: #dccdb8;
      --accent: #2b6b5f;
      --muted: #6d746f;
    }}
    body {{ margin: 0; color: var(--ink); background: linear-gradient(135deg, #dbece2, var(--bg) 48%, #efe1c9); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 34px 44px 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    section {{ margin: 18px 44px; padding: 20px; background: rgba(255, 250, 240, 0.94); border: 1px solid var(--line); border-radius: 18px; }}
    .banner {{ margin: 0 44px 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: #e6f1ec; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
    .metric {{ background: #f7ead6; border-radius: 14px; padding: 14px; }}
    .metric b {{ display: block; color: var(--accent); font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; text-align: left; }}
    th {{ color: var(--muted); }}
    code {{ background: #1f2926; color: #fffaf0; padding: 8px; border-radius: 8px; display: block; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <header>
    <h1>Phase 41 Research Follow-up Queue</h1>
    <p>Generated at {_e(payload.get('generated_at'))}. Static page; command examples are dry-run only.</p>
  </header>
  <div class="banner">{_e(SAFETY_BANNER)}</div>
  <section>
    <h2>Dashboard Summary</h2>
    <div class="grid">
      <div class="metric"><b>{_e(summary.get('followup_queue_items'))}</b>Follow-up items</div>
      <div class="metric"><b>{_e(summary.get('official_consensus_status'))}</b>Official consensus</div>
      <div class="metric"><b>{_e(summary.get('supplier_share_status'))}</b>Supplier share</div>
      <div class="metric"><b>{_e(summary.get('customer_allocation_status'))}</b>Customer allocation</div>
      <div class="metric"><b>{_e(summary.get('pending_created'))}</b>Pending created</div>
      <div class="metric"><b>{_e(summary.get('paper_order_created'))}</b>Paper orders</div>
    </div>
  </section>
  <section>
    <h2>Follow-up Queue</h2>
    <table><thead><tr><th>ID</th><th>Type</th><th>Priority</th><th>Route Status</th><th>Allowed Usage</th><th>Do Not Do</th></tr></thead>
    <tbody>{_item_rows(queue.get('items') or [])}</tbody></table>
  </section>
  <section>
    <h2>Source Availability Boundaries</h2>
    <ul>
      <li>Official consensus: {_e(official.get('status'))}; confirmed={_e(official.get('official_consensus_confirmed'))}</li>
      <li>Supplier share: {_e(supplier.get('status'))}; confirmed={_e(supplier.get('supplier_share_confirmed'))}</li>
      <li>Customer allocation: {_e(customer.get('status'))}; confirmed={_e(customer.get('customer_allocation_confirmed'))}</li>
    </ul>
  </section>
  <section>
    <h2>Dry-run Examples</h2>
    <code>python 08_scripts/jobs/execute_phase41_specific_evidence_requests.py --ticker 300308.SZ --dry-run --json</code>
    <code>python 08_scripts/reporting/build_phase41_research_followup_queue.py --ticker 300308.SZ --json</code>
  </section>
</body>
</html>
"""


def write_html(payload: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(payload), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 41 static follow-up HTML")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    output = write_html(payload, args.output)
    print(json.dumps({"output": str(output), "summary": (payload.get("dashboard") or {}).get("summary"), "safety": payload.get("safety")}, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
