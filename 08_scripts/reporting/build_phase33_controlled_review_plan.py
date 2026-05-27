#!/usr/bin/env python3
"""Build Phase 33 controlled evidence review execution plan."""

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
from smr_controlled_review_plan import build_controlled_review_plan

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, limit: int = 8) -> dict[str, Any]:
    return build_controlled_review_plan(conn, tickers=tickers, limit=limit)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 33 Controlled Evidence Review Plan",
        "",
        "## Summary",
        f"- Planned items: {summary.get('planned_items')}",
        f"- High priority: {summary.get('high_priority')}",
        f"- Sensitive items: {summary.get('sensitive_items')}",
        f"- Review required: {summary.get('review_required')}",
        f"- Request better source: {summary.get('request_better_source')}",
        "- Expected safety:",
        f"  - promotion allowed: {str(summary.get('promotion_allowed_expected')).lower()}",
        f"  - new pending: {str(summary.get('new_pending_expected')).lower()}",
        f"  - paper order: {str(summary.get('paper_order_expected')).lower()}",
        "",
        "## Planned Actions",
        "| Evidence ID | Ticker | Variable | Priority | Sensitive | Action | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in payload.get("plan_items") or []:
        reason = ", ".join(item.get("reason_for_selection") or [])
        lines.append(
            f"| {item.get('evidence_id')} | {item.get('ticker')} | {item.get('variable_type')} | {item.get('priority')} | {item.get('sensitive_variable')} | {item.get('recommended_action')} | {reason} |"
        )
    lines.extend(["", "## Skipped Items", "| Evidence | Reason |", "|---|---|"])
    for item in payload.get("skipped_items") or []:
        lines.append(f"| {item.get('evidence_id') or item.get('repair_task_id')} | {item.get('skip_reason')} |")
    if payload.get("warnings"):
        lines.extend(["", "## Warnings"])
        for warning in payload.get("warnings") or []:
            lines.append(f"- {warning}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 33 controlled review plan")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, limit=args.limit)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
