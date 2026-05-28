#!/usr/bin/env python3
"""Build Phase 36 focused evidence plan for 300308.SZ."""

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

from smr_agents import DB_PATH
from smr_evidence_acquisition_readiness import build_acquisition_readiness_score
from smr_evidence_acquisition_task import build_evidence_acquisition_tasks
from smr_research_quality_scoring import build_research_quality_score
from smr_targeted_evidence_gap import build_targeted_evidence_gap
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _priority_tasks(readiness: list[dict[str, Any]], tasks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    by_id = {str(task.get("task_id")): task for task in tasks}
    selected = []
    for rank, row in enumerate(readiness[:limit], start=1):
        task = by_id.get(str(row.get("task_id"))) or {}
        selected.append(
            {
                "rank": rank,
                "task_id": row.get("task_id"),
                "variable": row.get("variable"),
                "task_type": row.get("task_type"),
                "readiness_score": row.get("readiness_score"),
                "reason": row.get("reason"),
                "expected_impact": _expected_impact(str(row.get("variable") or ""), str(row.get("task_type") or "")),
                "allowed_usage_target": task.get("allowed_usage_target"),
            }
        )
    return selected


def _expected_impact(variable: str, task_type: str) -> str:
    if variable == "ASP_price_proxy":
        return "valuation_support_improved"
    if variable == "customer_allocation_proxy":
        return "bear_case_partially_mitigated"
    if variable == "official_consensus":
        return "expectation_gap_reference_improved"
    if variable in {"shipment", "order_visibility"}:
        return "evidence_chain_specificity_improved"
    if task_type == "MARK_NOT_PUBLICLY_CONFIRMABLE":
        return "uncertainty_boundary_clarified"
    return "research_packet_quality_improved"


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    ticker = "300308.SZ"
    gap = build_targeted_evidence_gap(conn, ticker)
    quality = build_research_quality_score(conn, ticker).get("research_quality") or {}
    tasks_payload = build_evidence_acquisition_tasks(conn, ticker)
    readiness_payload = build_acquisition_readiness_score(conn, ticker)
    critical = [
        row.get("variable")
        for row in (gap.get("targeted_evidence_gap") or {}).get("critical_missing_variables") or []
        if row.get("variable") in {"supplier_share", "ASP_price_proxy", "customer_allocation_proxy", "official_consensus"}
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "company_name": gap.get("company_name"),
        "focused_evidence_plan": {
            "research_quality_current": quality.get("overall_quality"),
            "target_quality": "medium",
            "target_status": "stronger_research_packet_not_pending",
            "critical_gaps": critical,
            "priority_tasks": _priority_tasks(
                readiness_payload.get("acquisition_readiness") or [],
                tasks_payload.get("evidence_acquisition_tasks") or [],
            ),
            "why_not_pending_after_plan": [
                "plan identifies tasks but does not complete evidence acquisition",
                "supplier share remains unconfirmed",
                "official consensus remains missing",
                "semantic evidence remains promotion-disabled",
            ],
        },
        "safety": {
            "plan_only": True,
            "investment_advice_generated": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    plan = payload.get("focused_evidence_plan") or {}
    lines = [
        "# Phase 36 300308 Focused Evidence Plan",
        "",
        f"## Ticker\n{payload.get('ticker')} / {payload.get('company_name')}",
        "",
        "## Overall",
        f"- Research quality current: {plan.get('research_quality_current')}",
        f"- Target quality: {plan.get('target_quality')}",
        f"- Target status: {plan.get('target_status')}",
        f"- Critical gaps: {', '.join(plan.get('critical_gaps') or [])}",
        "",
        "## Priority Tasks",
        "| Rank | Variable | Task | Score | Impact | Reason |",
        "|---:|---|---|---:|---|---|",
    ]
    for task in plan.get("priority_tasks") or []:
        lines.append(
            f"| {task.get('rank')} | {task.get('variable')} | {task.get('task_type')} | "
            f"{task.get('readiness_score')} | {task.get('expected_impact')} | {task.get('reason')} |"
        )
    lines.extend(["", "## Why Not Pending After Plan"])
    lines.extend(f"- {item}" for item in plan.get("why_not_pending_after_plan") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 36 focused evidence plan for 300308.SZ")
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
