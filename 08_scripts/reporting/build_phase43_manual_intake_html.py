#!/usr/bin/env python3
"""Generate a static read-only Phase 43 manual intake HTML page."""

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

from build_phase43_manual_intake_dashboard import build_payload as build_dashboard
from build_phase43_manual_intake_permission_audit import build_payload as build_permission
from build_phase43_manual_intake_review_queue import build_payload as build_queue
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFETY_BANNER = (
    "Phase 43 manual intake page is read-only: it does not confirm evidence, "
    "create pending review, create paper orders, relax promotion, or trade."
)


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    ticker = "300308.SZ"
    return {
        "generated_at": now_ts(),
        "dashboard": build_dashboard(conn),
        "permission_audit": build_permission(conn, ticker),
        "review_queue": build_queue(conn, ticker),
        "safety": {
            "html_is_read_only": True,
            "action_execution_enabled": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def _queue_rows(rows: list[dict[str, Any]]) -> str:
    rendered = []
    for row in rows:
        label = row.get("candidate_id") or row.get("rejection_id")
        rendered.append(
            "<tr>"
            f"<td>{_e(label)}</td>"
            f"<td>{_e(row.get('evidence_type'))}</td>"
            f"<td>{_e(row.get('confirmation_status'))}</td>"
            f"<td>{_e(row.get('allowed_usage'))}</td>"
            f"<td>{_e(row.get('recommended_action'))}</td>"
            "</tr>"
        )
    return "".join(rendered)


def render_html(payload: dict[str, Any]) -> str:
    dashboard = (payload.get("dashboard") or {}).get("summary") or {}
    permission = ((payload.get("permission_audit") or {}).get("permission_audit") or {})
    queue = ((payload.get("review_queue") or {}).get("manual_intake_review_queue") or {})
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 43 Manual Intake</title>
  <style>
    :root {{ --ink: #22302a; --paper: #fff8ec; --line: #d8c7a8; --accent: #2f6f5e; --soft: #e8efe4; }}
    body {{ margin: 0; color: var(--ink); background: radial-gradient(circle at 12% 10%, #d9ede5, transparent 30%), linear-gradient(135deg, #f8ebd0, #f4f1e8); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 36px 44px 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    section {{ margin: 18px 44px; padding: 20px; background: rgba(255, 248, 236, 0.94); border: 1px solid var(--line); border-radius: 18px; }}
    .banner {{ margin: 0 44px 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: #dfead8; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 12px; }}
    .metric {{ background: var(--soft); border-radius: 14px; padding: 14px; }}
    .metric b {{ display: block; color: var(--accent); font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; text-align: left; }}
    th {{ color: #657166; }}
  </style>
</head>
<body>
  <header>
    <h1>Phase 43 Manual Intake</h1>
    <p>Generated at {_e(payload.get('generated_at'))}. Manual inputs can become bounded candidates, not confirmed evidence.</p>
  </header>
  <div class="banner">{_e(SAFETY_BANNER)}</div>
  <section>
    <h2>Dashboard Summary</h2>
    <div class="grid">
      <div class="metric"><b>{_e(dashboard.get('payloads_checked'))}</b>Payloads checked</div>
      <div class="metric"><b>{_e(dashboard.get('candidates_created'))}</b>Candidates created</div>
      <div class="metric"><b>{_e(dashboard.get('candidates_written'))}</b>Candidates written</div>
      <div class="metric"><b>{_e(dashboard.get('rejections'))}</b>Rejections</div>
      <div class="metric"><b>{_e(dashboard.get('pending_created'))}</b>Pending created</div>
      <div class="metric"><b>{_e(dashboard.get('promotion_allowed_true'))}</b>Promotion allowed</div>
    </div>
  </section>
  <section>
    <h2>Permission Guard</h2>
    <ul>
      <li>Candidates checked: {_e(permission.get('manual_candidates_checked'))}</li>
      <li>Permission blocked: {_e(permission.get('permission_blocked'))}</li>
      <li>Allowed usage downgraded: {_e(permission.get('allowed_usage_downgraded'))}</li>
    </ul>
  </section>
  <section>
    <h2>Review Queue</h2>
    <table><thead><tr><th>Item</th><th>Evidence Type</th><th>Confirmation</th><th>Allowed Usage</th><th>Action</th></tr></thead>
    <tbody>{_queue_rows(queue.get('items') or [])}</tbody></table>
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
    parser = argparse.ArgumentParser(description="Build Phase 43 static manual intake HTML")
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
