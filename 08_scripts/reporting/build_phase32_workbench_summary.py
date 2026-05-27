#!/usr/bin/env python3
"""Build Phase 32 evidence review workbench summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parent
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, REPORTING_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase32_download_repair_workbench import build_payload as build_repair_workbench
from smr_agents import DB_PATH
from smr_evidence_review_workbench import build_workbench, dry_run_workbench_actions, filter_workbench_items
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    workbench = build_workbench(conn, tickers=tickers)
    high_items = filter_workbench_items(workbench.get("items") or [], priority="high")
    dry_run = dry_run_workbench_actions(conn, high_items)
    repair = build_repair_workbench(conn, tickers=tickers)
    summary = dict(workbench.get("summary") or {})
    summary["download_repair_tasks"] = max(summary.get("download_repair_tasks", 0), (repair.get("summary") or {}).get("repair_tasks", 0))
    summary["batch_dry_run_passed"] = (dry_run.get("summary") or {}).get("dry_run_actions_blocked", 0) == 0
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "next_review_recommendations": [
            f"Review {summary.get('high_priority', 0)} high-priority items first",
            f"Review {summary.get('sensitive_variable_items', 0)} sensitive variable items before linking",
            f"Handle {summary.get('download_repair_tasks', 0)} download repair tasks",
        ],
        "batch_dry_run_summary": dry_run.get("summary") or {},
        "safety": {
            "promotion_allowed_true": summary.get("promotion_allowed_true", 0),
            "new_pending_created": summary.get("new_pending_created", 0),
            "paper_order_created": summary.get("paper_order_created", 0),
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 32 Evidence Review Workbench Summary",
        "",
        "## Overall",
        f"- Total workbench items: {summary.get('total_workbench_items')}",
        f"- High priority: {summary.get('high_priority')}",
        f"- Sensitive variable items: {summary.get('sensitive_variable_items')}",
        f"- Review required: {summary.get('review_required')}",
        f"- Download repair tasks: {summary.get('download_repair_tasks')}",
        f"- Dry-run actions available: {summary.get('dry_run_actions_available')}",
        f"- Promotion allowed true: {summary.get('promotion_allowed_true')}",
        f"- New pending: {summary.get('new_pending_created')}",
        f"- Paper order created: {summary.get('paper_order_created')}",
        "",
        "## Recommended Review Order",
        "1. High priority items",
        "2. Sensitive variable items",
        "3. Review required item",
        "4. Download repair tasks",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 32 workbench summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
