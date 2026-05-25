#!/usr/bin/env python3
"""Build the Phase 15 daily review operations summary."""

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
from smr_human_review_workflow import list_review_queue
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts
from build_phase14_thesis_aware_daily_summary import build_summary_payload, latest_phase14_validation
from build_phase15_unknown_thesis_diagnostics import build_watchlist_payload


SCRIPT_NAME = "build_phase15_review_ops_summary.py"


def _approved_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM decision_ledger WHERE status='approved_paper'"
    ).fetchone()
    return int(row[0] or 0) if row else 0


def _needs_more_research_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM decision_ledger WHERE status='needs_more_research'"
    ).fetchone()
    return int(row[0] or 0) if row else 0


def _review_focus(item: dict[str, Any]) -> list[str]:
    focus = []
    bear = item.get("bear_case_gate") or {}
    if bear.get("overall_status") in {"partially_mitigated", "unresolved"}:
        focus.append("bear case residual risk")
    if item.get("optional_warnings"):
        focus.append("optional capex/free_cash_flow warnings")
    focus.append("portfolio exposure after approval")
    return list(dict.fromkeys(focus))


def build_ops_payload(conn: sqlite3.Connection, watchlist_id: str) -> dict[str, Any]:
    validation = latest_phase14_validation(conn, watchlist_id)
    phase14 = build_summary_payload(validation, watchlist_id) if validation else {"summary": {}, "ticker_rows": []}
    queue = list_review_queue(conn)
    pending = [item for item in queue if item.get("status") == "pending_human_review"]
    reduced = [item for item in pending if item.get("promotion_mode") == "reduced_size_pending"]
    unknown_payload = build_watchlist_payload(conn, watchlist_id)
    core_rows = phase14.get("core_blockers") or []
    unknown_rows = unknown_payload.get("items") or []
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist_id,
        "summary": {
            "pending_human_review": len(pending),
            "reduced_size_pending": len(reduced),
            "approved_paper": _approved_count(conn),
            "needs_more_research": _needs_more_research_count(conn),
            "core_blocker_tickers": [row.get("ticker") for row in core_rows],
            "unknown_thesis_tickers": [row.get("ticker") for row in unknown_rows],
        },
        "review_actions_needed": [
            {
                "ticker": item.get("ticker"),
                "recommendation_id": item.get("recommendation_id"),
                "action": "review_reduced_size_pending" if item.get("promotion_mode") == "reduced_size_pending" else "review_pending_human_review",
                "suggested_review_focus": _review_focus(item),
                "paper_order_allowed": item.get("paper_order_allowed"),
            }
            for item in pending
        ],
        "repair_actions_needed": [
            {
                "ticker": row.get("ticker"),
                "action": "repair_core_blocker",
                "field": ", ".join(row.get("core_blockers") or []),
            }
            for row in core_rows
        ] + [
            {
                "ticker": row.get("ticker"),
                "action": "fix_unknown_thesis_metadata",
                "field": "primary_thesis_type",
                "suggested_metadata_patch": row.get("suggested_metadata_patch"),
            }
            for row in unknown_rows
        ],
        "paper_order_guard": [
            {
                "ticker": item.get("ticker"),
                "status": item.get("status"),
                "promotion_mode": item.get("promotion_mode"),
                "paper_order_allowed": item.get("paper_order_allowed"),
                "requires_human_review": item.get("requires_human_review"),
            }
            for item in queue
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 15 Review Operations Summary",
        "",
        "## Pending Human Review",
        "| Ticker | Thesis | Mode | Position | Main Warnings | Suggested Review Focus |",
        "|---|---|---|---:|---|---|",
    ]
    for item in payload.get("review_actions_needed") or []:
        warnings = "-"
        focus = ", ".join(item.get("suggested_review_focus") or []) or "-"
        lines.append(f"| {item.get('ticker')} | - | {item.get('action')} | - | {warnings} | {focus} |")
    lines.extend([
        "",
        "## Core Blocker Recovery",
        "| Ticker | Core Blocker | Suggested Fix |",
        "|---|---|---|",
    ])
    for item in payload.get("repair_actions_needed") or []:
        if item.get("action") == "repair_core_blocker":
            lines.append(f"| {item.get('ticker')} | {item.get('field')} | repair core field evidence |")
    lines.extend([
        "",
        "## Unknown Thesis",
        "| Ticker | Reason | Suggested Metadata Patch |",
        "|---|---|---|",
    ])
    for item in payload.get("repair_actions_needed") or []:
        if item.get("action") == "fix_unknown_thesis_metadata":
            lines.append(f"| {item.get('ticker')} | unknown thesis | {json.dumps(item.get('suggested_metadata_patch'), ensure_ascii=False)} |")
    lines.extend([
        "",
        "## Paper Order Guard",
        "| Ticker | Status | Paper Order Allowed |",
        "|---|---|---|",
    ])
    for item in payload.get("paper_order_guard") or []:
        lines.append(f"| {item.get('ticker')} | {item.get('status')} | {item.get('paper_order_allowed')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 15 review operations summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_ops_payload(conn, args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase15_review_ops_summary",
            entity_id=args.watchlist,
            status="updated",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase15 review ops summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
