#!/usr/bin/env python3
"""Generate a static read-only Phase 44 closeout HTML page."""

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

from build_phase44_closeout_dashboard import build_payload as build_dashboard
from build_phase44_manual_candidate_final_usage_matrix import build_payload as build_matrix
from build_phase44_mainline_transition_plan import build_payload as build_transition
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFETY_BANNER = (
    "Phase 44 closeout page is read-only: it does not confirm evidence, "
    "create pending review, create paper orders, relax promotion, or trade."
)


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    ticker = "300308.SZ"
    return {
        "generated_at": now_ts(),
        "dashboard": build_dashboard(conn),
        "final_usage_matrix": build_matrix(conn, ticker),
        "transition_plan": build_transition(),
        "safety": {
            "html_is_read_only": True,
            "action_execution_enabled": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def _usage_rows(rows: list[dict[str, Any]]) -> str:
    rendered = []
    for row in rows:
        rendered.append(
            "<tr>"
            f"<td>{_e(row.get('candidate_type'))}</td>"
            f"<td>{_e(row.get('review_status'))}</td>"
            f"<td>{_e(row.get('confirmation_status'))}</td>"
            f"<td>{_e(row.get('final_allowed_usage'))}</td>"
            "</tr>"
        )
    return "".join(rendered)


def render_html(payload: dict[str, Any]) -> str:
    dashboard = (payload.get("dashboard") or {}).get("summary") or {}
    matrix = ((payload.get("final_usage_matrix") or {}).get("manual_candidate_final_usage_matrix") or {})
    transition = ((payload.get("transition_plan") or {}).get("mainline_transition_plan") or {})
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 44 Manual Candidate Closeout</title>
  <style>
    :root {{ --ink: #27302f; --paper: #fff8ea; --line: #d7c4a2; --accent: #7a4b20; --soft: #ece3cf; }}
    body {{ margin: 0; color: var(--ink); background: radial-gradient(circle at 18% 8%, #dfefe8, transparent 28%), linear-gradient(135deg, #f6ead1, #f3efe6); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 36px 44px 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    section {{ margin: 18px 44px; padding: 20px; background: rgba(255, 248, 234, 0.94); border: 1px solid var(--line); border-radius: 18px; }}
    .banner {{ margin: 0 44px 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: #efddbd; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 12px; }}
    .metric {{ background: var(--soft); border-radius: 14px; padding: 14px; }}
    .metric b {{ display: block; color: var(--accent); font-size: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; text-align: left; }}
    th {{ color: #6f6557; }}
  </style>
</head>
<body>
  <header>
    <h1>Phase 44 Manual Candidate Closeout</h1>
    <p>Generated at {_e(payload.get('generated_at'))}. Manual intake governance is closed and returns to the research mainline.</p>
  </header>
  <div class="banner">{_e(SAFETY_BANNER)}</div>
  <section>
    <h2>Closeout Summary</h2>
    <div class="grid">
      <div class="metric"><b>{_e(dashboard.get('manual_candidates_reviewed'))}</b>Reviewed candidates</div>
      <div class="metric"><b>{_e(dashboard.get('audit_records'))}</b>Audit records</div>
      <div class="metric"><b>{_e(dashboard.get('confirmed_variables_added'))}</b>Confirmed variables</div>
      <div class="metric"><b>{_e(dashboard.get('pending_created'))}</b>Pending created</div>
      <div class="metric"><b>{_e(dashboard.get('paper_order_created'))}</b>Paper orders</div>
      <div class="metric"><b>{_e(dashboard.get('manual_intake_branch_status'))}</b>Branch status</div>
    </div>
  </section>
  <section>
    <h2>Final Usage Matrix</h2>
    <table><thead><tr><th>Candidate</th><th>Review Status</th><th>Confirmation</th><th>Final Usage</th></tr></thead>
    <tbody>{_usage_rows(matrix.get('rows') or [])}</tbody></table>
  </section>
  <section>
    <h2>Next Mainline Step</h2>
    <p>{_e(transition.get('next_phase'))}: {_e(transition.get('phase45_goal'))}</p>
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
    parser = argparse.ArgumentParser(description="Build Phase 44 static closeout HTML")
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
