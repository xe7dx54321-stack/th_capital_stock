#!/usr/bin/env python3
"""Build Phase 33 controlled review execution summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase33_controlled_review_plan import build_payload as build_plan
from build_phase33_lifecycle_delta_report import build_payload as build_lifecycle_delta
from build_phase33_workbench_incremental_view import build_payload as build_incremental_view
from smr_agents import DB_PATH
from smr_controlled_review_plan import PHASE33_REASON_PREFIX
from smr_download_repair_queue import list_download_repair_tasks
from validate_phase33_post_review_research_impact import build_payload as build_research_impact
from validate_phase33_sensitive_guard_post_execution import build_payload as build_sensitive_guard
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    plan = build_plan(conn)
    delta = build_lifecycle_delta(conn)
    incremental = build_incremental_view(conn)
    sensitive = build_sensitive_guard(conn)
    impact = build_research_impact(conn)
    repair_tasks = list_download_repair_tasks(conn)
    delta_summary = delta.get("summary") or {}
    impact_summary = impact.get("summary") or {}
    sensitive_summary = sensitive.get("summary") or {}
    action_repair_tasks = [task for task in repair_tasks if str(task.get("reason") or "").startswith(PHASE33_REASON_PREFIX)]
    controlled_upsert_tasks = [task for task in repair_tasks if task not in action_repair_tasks]
    summary = {
        "planned_actions": (plan.get("summary") or {}).get("planned_actions", 0),
        "actions_executed": delta_summary.get("audit_records", 0),
        "actions_blocked": 0,
        "audit_records_written": delta_summary.get("audit_records", 0),
        "lifecycle_status_updated": delta_summary.get("audit_records", 0),
        "repair_tasks_written": len(controlled_upsert_tasks),
        "review_action_repair_tasks": len(action_repair_tasks),
        "repair_tasks_total": len(repair_tasks),
        "sensitive_guard_violations": sensitive_summary.get("violations", 0),
        "confirmed_variables_added": impact_summary.get("confirmed_variables_added", 0),
        "promotion_allowed_true": delta_summary.get("promotion_allowed_true_delta", 0),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "executed_actions": delta.get("rows") or [],
        "remaining_review_queue": (incremental.get("summary") or {}),
        "next_steps": [
            "Continue reviewing remaining high-priority items",
            "Handle needs_better_source tasks",
            "Do not promote semantic evidence without full gate validation",
        ],
        "safety": {
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    remaining = payload.get("remaining_review_queue") or {}
    lines = [
        "# Phase 33 Controlled Evidence Review Execution Summary",
        "",
        "## Overall",
        f"- Planned actions: {summary.get('planned_actions')}",
        f"- Actions executed: {summary.get('actions_executed')}",
        f"- Actions blocked: {summary.get('actions_blocked')}",
        f"- Audit records written: {summary.get('audit_records_written')}",
        f"- Lifecycle updated: {summary.get('lifecycle_status_updated')}",
        f"- Repair tasks written: {summary.get('repair_tasks_written')}",
        f"- Sensitive violations: {summary.get('sensitive_guard_violations')}",
        f"- Confirmed variables added: {summary.get('confirmed_variables_added')}",
        f"- Promotion allowed true: {summary.get('promotion_allowed_true')}",
        f"- New pending: {summary.get('new_pending_created')}",
        f"- Paper order: {summary.get('paper_order_created')}",
        "",
        "## Executed Actions",
        "| Evidence | Action | Before | After | Audit |",
        "|---|---|---|---|---|",
    ]
    for row in payload.get("executed_actions") or []:
        lines.append(
            f"| {row.get('evidence_id')} | {row.get('action')} | {row.get('before_lifecycle_status')} | {row.get('after_lifecycle_status')} | {row.get('audit_id')} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Review Queue",
            "| Category | Count |",
            "|---|---|",
            f"| Remaining items | {remaining.get('remaining_items')} |",
            f"| Remaining high priority | {remaining.get('remaining_high_priority')} |",
            f"| Remaining sensitive items | {remaining.get('remaining_sensitive_items')} |",
            f"| Needs better source | {remaining.get('needs_better_source')} |",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 33 controlled review execution summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
