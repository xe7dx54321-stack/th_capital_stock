#!/usr/bin/env python3
"""Build Phase 36 evidence acquisition dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from build_phase36_300308_focused_evidence_plan import build_payload as build_300308_plan
from build_phase36_300394_evidence_repair_plan import build_payload as build_300394_repair
from smr_agents import DB_PATH
from smr_evidence_acquisition_readiness import build_acquisition_readiness_score
from smr_evidence_acquisition_task import build_evidence_acquisition_tasks
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    tasks_300308 = build_evidence_acquisition_tasks(conn, "300308.SZ")
    readiness = build_acquisition_readiness_score(conn, "300308.SZ")
    plan_300308 = build_300308_plan(conn)
    repair_300394 = build_300394_repair(conn)
    repair_steps = (repair_300394.get("evidence_repair_plan") or {}).get("recommended_steps") or []
    top_tasks = (plan_300308.get("focused_evidence_plan") or {}).get("priority_tasks") or []
    summary = {
        "target_tickers": ["300308.SZ", "300394.SZ"],
        "300308_priority_tasks": len(tasks_300308.get("evidence_acquisition_tasks") or []),
        "300394_repair_tasks": len(repair_steps),
        "high_priority_tasks": (tasks_300308.get("summary") or {}).get("high_priority_tasks", 0),
        "manual_research_required": (tasks_300308.get("summary") or {}).get("manual_research_required", 0),
        "not_publicly_confirmable": (tasks_300308.get("summary") or {}).get("not_publicly_confirmable", 0),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "ticker_rows": [
            {
                "ticker": "300308.SZ",
                "mode": "targeted_acquisition_plan",
                "top_tasks": [
                    f"{task.get('variable')} via {task.get('task_type')}"
                    for task in top_tasks[:3]
                ],
                "top_readiness_bucket": ((readiness.get("acquisition_readiness") or [{}])[0]).get("readiness_bucket"),
            },
            {
                "ticker": "300394.SZ",
                "mode": "evidence_chain_repair",
                "top_tasks": [step.get("task") for step in repair_steps[:3]],
                "diagnostic_status": (repair_300394.get("evidence_repair_plan") or {}).get("diagnostic_status"),
            },
        ],
        "safety": {
            "dashboard_is_investment_advice": False,
            "fetch_executed": False,
            "evidence_written": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 36 Evidence Acquisition Dashboard",
        "",
        "## Summary",
        f"- Target tickers: {', '.join(summary.get('target_tickers') or [])}",
        f"- 300308 priority tasks: {summary.get('300308_priority_tasks')}",
        f"- 300394 repair tasks: {summary.get('300394_repair_tasks')}",
        f"- High priority tasks: {summary.get('high_priority_tasks')}",
        f"- Manual research required: {summary.get('manual_research_required')}",
        f"- Not publicly confirmable: {summary.get('not_publicly_confirmable')}",
        f"- New pending created: {summary.get('new_pending_created')}",
        f"- Paper order created: {summary.get('paper_order_created')}",
        "",
        "## By Ticker",
        "| Ticker | Mode | Top Tasks |",
        "|---|---|---|",
    ]
    for row in payload.get("ticker_rows") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('mode')} | {'; '.join(row.get('top_tasks') or [])} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 evidence acquisition dashboard")
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
