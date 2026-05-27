#!/usr/bin/env python3
"""Build Phase 33 workbench incremental view."""

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

from smr_controlled_review_plan import phase33_audits
from smr_agents import DB_PATH
from smr_evidence_review_workbench import build_workbench, recommended_first_pass_items
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _reviewed_rows(audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in audits:
        rows.append(
            {
                "evidence_id": row.get("evidence_id"),
                "ticker": row.get("ticker"),
                "action": row.get("action"),
                "before_lifecycle_status": row.get("before_status"),
                "after_lifecycle_status": row.get("after_status"),
                "reviewed_at": row.get("created_at"),
            }
        )
    return rows


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    workbench = build_workbench(conn, tickers=tickers)
    audits = phase33_audits(conn)
    reviewed_ids = {row.get("evidence_id") for row in audits}
    remaining = [item for item in workbench.get("items") or [] if item.get("evidence_id") not in reviewed_ids]
    next_items = recommended_first_pass_items(remaining)[:8]
    needs_better_source = sum(1 for row in audits if row.get("after_status") == "needs_better_source")
    summary = {
        "total_workbench_items": (workbench.get("summary") or {}).get("total_workbench_items", len(workbench.get("items") or [])),
        "reviewed_items": len(reviewed_ids),
        "remaining_items": len(remaining),
        "remaining_high_priority": sum(1 for item in remaining if item.get("priority") == "high"),
        "remaining_sensitive_items": sum(1 for item in remaining if item.get("sensitive_variable")),
        "needs_better_source": needs_better_source,
        "next_recommended_items": len(next_items),
        "promotion_allowed_true": 0,
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "reviewed_items": _reviewed_rows(audits),
        "next_recommended_items": [
            {
                "workbench_item_id": item.get("workbench_item_id"),
                "evidence_id": item.get("evidence_id"),
                "ticker": item.get("ticker"),
                "priority": item.get("priority"),
                "variable_type": item.get("variable_type"),
                "sensitive_variable": item.get("sensitive_variable"),
                "recommended_action": item.get("recommended_action"),
            }
            for item in next_items
        ],
        "safety": {
            "read_only_incremental_view": True,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 33 Workbench Incremental View",
        "",
        "## Summary",
        f"- Total workbench items: {summary.get('total_workbench_items')}",
        f"- Reviewed items: {summary.get('reviewed_items')}",
        f"- Remaining items: {summary.get('remaining_items')}",
        f"- Remaining high priority: {summary.get('remaining_high_priority')}",
        f"- Remaining sensitive items: {summary.get('remaining_sensitive_items')}",
        f"- Needs better source: {summary.get('needs_better_source')}",
        f"- Next recommended items: {summary.get('next_recommended_items')}",
        "",
        "## Reviewed Items",
        "| Evidence | Ticker | Action | Before | After | Reviewed At |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload.get("reviewed_items") or []:
        lines.append(
            f"| {row.get('evidence_id')} | {row.get('ticker')} | {row.get('action')} | {row.get('before_lifecycle_status')} | {row.get('after_lifecycle_status')} | {row.get('reviewed_at')} |"
        )
    lines.extend(["", "## Next Recommended Items", "| Evidence | Ticker | Priority | Variable | Sensitive | Action |", "|---|---|---|---|---|---|"])
    for row in payload.get("next_recommended_items") or []:
        lines.append(
            f"| {row.get('evidence_id')} | {row.get('ticker')} | {row.get('priority')} | {row.get('variable_type')} | {row.get('sensitive_variable')} | {row.get('recommended_action')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 33 workbench incremental view")
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
