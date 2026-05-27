#!/usr/bin/env python3
"""Build Phase 31 evidence review queue."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_evidence_review_queue import build_review_queue_with_generated_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, ticker: str | None = None) -> dict:
    selected = ticker or tickers
    queue = build_review_queue_with_generated_candidates(conn, tickers=selected)
    return {
        "generated_at": now_ts(),
        "summary": queue.get("summary") or {},
        "items": queue.get("items") or [],
        "safety": {
            "promotion_allowed_true": (queue.get("summary") or {}).get("promotion_allowed_true", 0),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 31 Evidence Review Queue",
        "",
        "## Overall",
        f"- Review queue items: {summary.get('review_queue_items')}",
        f"- High priority: {summary.get('high_priority')}",
        f"- Medium priority: {summary.get('medium_priority')}",
        f"- Low priority: {summary.get('low_priority')}",
        f"- Sensitive variable items: {summary.get('sensitive_variable_items')}",
        f"- Promotion allowed true: {summary.get('promotion_allowed_true')}",
        "",
        "## Queue",
        "| Priority | Type | Ticker | Evidence | Variable | Reason | Recommended Action |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in payload.get("items") or []:
        reason = ", ".join(item.get("review_reason") or [])
        lines.append(
            f"| {item.get('priority')} | {item.get('item_type')} | {item.get('ticker')} | {item.get('evidence_id') or item.get('source_id')} | {item.get('variable_type') or ''} | {reason} | {item.get('recommended_action')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 31 evidence review queue")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--ticker")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, ticker=args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
