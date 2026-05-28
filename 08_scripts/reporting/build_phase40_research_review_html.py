#!/usr/bin/env python3
"""Generate a static read-only Phase 40 research review HTML workbench."""

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

from build_phase39_300394_repair_status_summary import build_payload as build_repair_status
from build_phase40_research_review_dashboard import build_payload as build_dashboard
from build_phase40_research_review_queue import build_payload as build_queue
from build_phase40_research_review_workbench_packet import build_payload as build_workbench_packet
from smr_agents import DB_PATH
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


SAFETY_BANNER = (
    "Phase 40 research review workbench is read-only: no pending creation, "
    "no paper order, no promotion relaxation, and no trade execution."
)


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "generated_at": now_ts(),
        "queue": build_queue(conn),
        "workbench_packet": build_workbench_packet(conn, "300308.SZ"),
        "dashboard": build_dashboard(conn),
        "repair_status": build_repair_status(conn),
        "safety": {
            "html_is_read_only": True,
            "action_execution_enabled": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def _list(items: list[Any]) -> str:
    return "".join(f"<li>{_e(item)}</li>" for item in items)


def render_html(payload: dict[str, Any]) -> str:
    queue = payload.get("queue") or {}
    workbench = ((payload.get("workbench_packet") or {}).get("research_review_workbench_packet") or {})
    dashboard = payload.get("dashboard") or {}
    repair = ((payload.get("repair_status") or {}).get("repair_status_summary") or {})
    summary = queue.get("summary") or {}
    evidence_summary = workbench.get("evidence_strengthened_summary") or {}
    why = workbench.get("why_not_pending") or []
    checklist = workbench.get("human_checklist") or []
    allowed = workbench.get("allowed_review_actions") or []
    forbidden = [
        "approve_pending",
        "approve_paper",
        "create_order",
        "create_position",
        "promote_to_investment_candidate",
        "confirm_supplier_share",
        "confirm_customer_allocation",
        "confirm_official_consensus",
    ]
    checklist_html = "".join(
        f"<li><strong>{_e(item.get('question'))}</strong><br><span>{_e(', '.join(item.get('evidence_to_review') or item.get('evidence_gap') or []))}</span></li>"
        for item in checklist
    )
    why_html = "".join(
        f"<li><strong>{_e(item.get('blocker'))}</strong>: {_e(item.get('why_it_still_matters'))}</li>"
        for item in why
    )
    dry_runs = [
        "python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_deeper_research --dry-run --json",
        "python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action request_specific_evidence --evidence-type official_consensus --dry-run --json",
        "python 08_scripts/jobs/apply_phase40_research_review_action.py --ticker 300308.SZ --action mark_reviewed --dry-run --json",
    ]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 40 Research Review Workbench</title>
  <style>
    :root {{
      --bg: #f4efe3;
      --ink: #1d2a26;
      --card: #fffaf0;
      --line: #d8cab4;
      --accent: #1f6b5f;
      --muted: #69746f;
      --warn: #8f3b1f;
    }}
    body {{ margin: 0; color: var(--ink); background: radial-gradient(circle at 15% 0%, #d8eadf, var(--bg) 38%, #efe3cf); font-family: Georgia, "Times New Roman", serif; }}
    header {{ padding: 34px 44px 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; }}
    h2 {{ margin: 0 0 12px; }}
    section {{ margin: 18px 44px; padding: 20px; background: rgba(255, 250, 240, 0.92); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 14px 34px rgba(35, 28, 18, 0.08); }}
    .banner {{ margin: 0 44px 18px; padding: 16px 18px; border-left: 6px solid var(--accent); background: #e7f2ec; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
    .metric {{ padding: 14px; background: #f8ecd9; border-radius: 14px; }}
    .metric b {{ display: block; color: var(--accent); font-size: 24px; }}
    code {{ display: block; white-space: pre-wrap; word-break: break-word; background: #1d2a26; color: #f8ecd9; padding: 10px; border-radius: 10px; margin: 8px 0; }}
    li {{ margin: 7px 0; }}
    .muted {{ color: var(--muted); }}
    .warn {{ color: var(--warn); font-weight: 700; }}
  </style>
</head>
<body>
  <header>
    <h1>Phase 40 Research Review Workbench</h1>
    <p class="muted">Generated at {_e(payload.get('generated_at'))}. Static local page; no action execution is wired into this HTML.</p>
  </header>
  <div class="banner">{_e(SAFETY_BANNER)}</div>
  <section>
    <h2>Queue Summary</h2>
    <div class="grid">
      <div class="metric"><b>{_e(summary.get('queue_items'))}</b>Research review queue items</div>
      <div class="metric"><b>{_e(summary.get('repair_required'))}</b>Repair-only rows</div>
      <div class="metric"><b>{_e(summary.get('pending_allowed_true'))}</b>Pending allowed true</div>
      <div class="metric"><b>{_e(summary.get('paper_order_allowed_true'))}</b>Paper order allowed true</div>
    </div>
  </section>
  <section>
    <h2>300308 Research Review Packet</h2>
    <p>Status: <strong>{_e(workbench.get('review_candidate_status'))}</strong></p>
    <p>Evidence: {_e(evidence_summary.get('evidence_before'))} to {_e(evidence_summary.get('evidence_after'))}; new evidence count {_e(evidence_summary.get('new_evidence_count'))}.</p>
    <p>Strengthened variables: {_e(', '.join(evidence_summary.get('strengthened_variables') or []))}</p>
  </section>
  <section>
    <h2>Human Review Checklist</h2>
    <ol>{checklist_html}</ol>
  </section>
  <section>
    <h2>Why Not Pending</h2>
    <ul>{why_html}</ul>
  </section>
  <section>
    <h2>Allowed Actions</h2>
    <ul>{_list(allowed)}</ul>
    <h2>Explicit Forbidden Actions</h2>
    <ul class="warn">{_list(forbidden)}</ul>
  </section>
  <section>
    <h2>Dry-Run Command Examples</h2>
    {''.join(f'<code>{_e(command)}</code>' for command in dry_runs)}
  </section>
  <section>
    <h2>300394 Repair Status</h2>
    <p>Status: <strong>{_e(repair.get('current_status'))}</strong></p>
    <p>Research deepening allowed: {_e(repair.get('research_deepening_allowed'))}</p>
    <p>Dashboard safety: {_e((dashboard.get('summary') or {}).get('promotion_allowed_true'))} promotion-allowed rows.</p>
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
    parser = argparse.ArgumentParser(description="Build Phase 40 static research review HTML")
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
