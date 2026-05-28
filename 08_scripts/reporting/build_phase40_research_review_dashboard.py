#!/usr/bin/env python3
"""Build Phase 40 research review dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_research_review_queue import build_payload as build_queue
from smr_agents import DB_PATH
from smr_research_review_lifecycle import get_lifecycle_by_ticker, list_lifecycles
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _status_for_300308(conn: sqlite3.Connection, queue_items: list[dict]) -> str:
    lifecycle = get_lifecycle_by_ticker(conn, "300308.SZ")
    if lifecycle:
        return str(lifecycle.get("research_review_status"))
    if queue_items:
        return str(queue_items[0].get("status"))
    return "not_ready_for_research_review"


def build_payload(conn: sqlite3.Connection) -> dict:
    queue = build_queue(conn)
    items = queue.get("items") or []
    repair_rows = queue.get("repair_rows") or []
    lifecycles = list_lifecycles(conn)
    counts = Counter(row.get("research_review_status") for row in lifecycles)
    status_300308 = _status_for_300308(conn, items)
    requests = list_specific_evidence_requests(conn)
    why_not_pending = (items[0].get("why_not_pending") if items else []) or [
        "supplier_share_unconfirmed",
        "official_consensus_missing",
        "confirmed_customer_allocation_missing",
    ]
    return {
        "generated_at": now_ts(),
        "summary": {
            "research_review_queue_items": (queue.get("summary") or {}).get("queue_items", 0),
            "in_research_review": counts.get("in_research_review", 0),
            "reviewed_request_deeper_research": counts.get("reviewed_request_deeper_research", 0),
            "reviewed_continue_evidence": counts.get("reviewed_continue_evidence", 0),
            "reviewed_deprioritize": counts.get("reviewed_deprioritize", 0),
            "repair_required_before_review": (queue.get("summary") or {}).get("repair_required", 0),
            "specific_evidence_requests_open": sum(1 for row in requests if row.get("status") == "open"),
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
        },
        "ticker_rows": [
            {
                "ticker": "300308.SZ",
                "status": status_300308,
                "recommended_action": "request_deeper_research"
                if status_300308 == "research_review_candidate"
                else "continue_research_review_follow_up",
                "why_not_pending": why_not_pending,
            },
            {
                "ticker": "300394.SZ",
                "status": (repair_rows[0].get("status") if repair_rows else "repair_required_before_review"),
                "recommended_action": "repair_evidence_chain",
            },
        ],
        "safety": {
            "pending_human_review_created": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = ["# Phase 40 Research Review Dashboard", "", "## Summary"]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Ticker Rows", "| Ticker | Status | Recommended Action |", "|---|---|---|"])
    for row in payload.get("ticker_rows") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('status')} | {row.get('recommended_action')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 40 research review dashboard")
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
