#!/usr/bin/env python3
"""Generate a static read-only Phase 42 fulfillment HTML page."""

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

from build_phase42_customer_allocation_proxy_audit import build_payload as build_customer_audit
from build_phase42_followup_fulfillment_packet import build_payload as build_packet
from build_phase42_followup_fulfillment_state import build_payload as build_state
from build_phase42_fulfillment_dashboard import build_payload as build_dashboard
from build_phase42_official_consensus_fulfillment import build_payload as build_official
from build_phase42_supplier_share_scenario_registry import build_payload as build_supplier
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFETY_BANNER = (
    "Phase 42 fulfillment page is read-only: it does not ingest raw sources, write evidence, "
    "create pending review, create paper orders, relax promotion, or trade."
)


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    ticker = "300308.SZ"
    return {
        "generated_at": now_ts(),
        "state": build_state(conn, ticker),
        "official_consensus": build_official(conn, ticker),
        "supplier_share": build_supplier(conn, ticker),
        "customer_allocation": build_customer_audit(conn, ticker),
        "packet": build_packet(conn, ticker),
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


def _request_rows(rows: list[dict[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{_e(row.get('request_type'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            f"<td>{_e(row.get('current_evidence_status'))}</td>"
            f"<td>{_e(row.get('allowed_usage'))}</td>"
            f"<td>{_e(row.get('next_action'))}</td>"
            "</tr>"
        )
    return "".join(rendered)


def render_html(payload: dict[str, Any]) -> str:
    dashboard = (payload.get("dashboard") or {}).get("summary") or {}
    state = ((payload.get("state") or {}).get("followup_fulfillment_state") or {})
    packet = ((payload.get("packet") or {}).get("followup_fulfillment_packet") or {})
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 42 Follow-up Fulfillment</title>
  <style>
    :root {{ --ink: #25302d; --paper: #fff9ea; --line: #d7c7aa; --accent: #8a4b22; --soft: #efe3cd; }}
    body {{ margin: 0; color: var(--ink); background: radial-gradient(circle at 12% 8%, #e2efe6, transparent 32%), linear-gradient(135deg, #f7ead0, #f4f0e8); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 36px 44px 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    section {{ margin: 18px 44px; padding: 20px; background: rgba(255, 249, 234, 0.94); border: 1px solid var(--line); border-radius: 18px; }}
    .banner {{ margin: 0 44px 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: #f3dfc3; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 12px; }}
    .metric {{ background: var(--soft); border-radius: 14px; padding: 14px; }}
    .metric b {{ display: block; color: var(--accent); font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; text-align: left; }}
    th {{ color: #6b6255; }}
  </style>
</head>
<body>
  <header>
    <h1>Phase 42 Follow-up Fulfillment</h1>
    <p>Generated at {_e(payload.get('generated_at'))}. Manual source intake remains template/validation only.</p>
  </header>
  <div class="banner">{_e(SAFETY_BANNER)}</div>
  <section>
    <h2>Dashboard Summary</h2>
    <div class="grid">
      <div class="metric"><b>{_e(dashboard.get('followup_requests'))}</b>Follow-up requests</div>
      <div class="metric"><b>{_e(dashboard.get('authorized_source_required'))}</b>Authorized source required</div>
      <div class="metric"><b>{_e(dashboard.get('scenario_only'))}</b>Scenario only</div>
      <div class="metric"><b>{_e(dashboard.get('proxy_only'))}</b>Proxy only</div>
      <div class="metric"><b>{_e(dashboard.get('pending_created'))}</b>Pending created</div>
      <div class="metric"><b>{_e(dashboard.get('paper_order_created'))}</b>Paper orders</div>
    </div>
  </section>
  <section>
    <h2>Fulfillment State</h2>
    <table><thead><tr><th>Request</th><th>Status</th><th>Evidence Status</th><th>Allowed Usage</th><th>Next Action</th></tr></thead>
    <tbody>{_request_rows(state.get('request_rows') or [])}</tbody></table>
  </section>
  <section>
    <h2>Research Impact</h2>
    <ul>
      <li>Overall fulfillment: {_e(packet.get('overall_fulfillment'))}</li>
      <li>Research impact: {_e(packet.get('research_impact'))}</li>
      <li>Pending allowed: {_e(packet.get('pending_allowed'))}</li>
    </ul>
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
    parser = argparse.ArgumentParser(description="Build Phase 42 static fulfillment HTML")
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
