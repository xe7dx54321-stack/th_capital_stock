#!/usr/bin/env python3
"""Build Phase 44 manual candidate review audit report."""

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
from smr_manual_candidate_review_audit import list_manual_candidate_review_audits
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    records = list_manual_candidate_review_audits(conn, ticker=ticker)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_candidate_review_audit": {
            "audit_records": len(records),
            "usable_for_promotion_true": sum(1 for row in records if row.get("usable_for_promotion")),
            "pending_created": sum(1 for row in records if row.get("pending_created")),
            "paper_order_created": sum(1 for row in records if row.get("paper_order_created")),
            "records": records,
        },
        "safety": {
            "raw_file_recorded": False,
            "promotion_triggered": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("manual_candidate_review_audit") or {}
    lines = [f"# Phase 44 Manual Candidate Review Audit: {payload.get('ticker')}", "", "## Summary"]
    for key in ("audit_records", "usable_for_promotion_true", "pending_created", "paper_order_created"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Records"])
    for row in body.get("records") or []:
        lines.append(f"- {row.get('candidate_type')}: {row.get('action')} / {row.get('before_status')} -> {row.get('after_status')}")
        lines.append(f"  Confirmation: {row.get('confirmation_status_after_action')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 44 manual candidate review audit")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
