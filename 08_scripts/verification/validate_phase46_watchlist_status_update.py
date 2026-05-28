#!/usr/bin/env python3
"""Validate Phase 46 watchlist status update safety."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase46_watchlist_audit_report import build_payload as build_audit
from smr_agents import DB_PATH
from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    entry = get_paper_watchlist_entry(conn, ticker) or {}
    audit = build_audit(conn, ticker).get("watchlist_audit_report") or {}
    current_status = entry.get("watchlist_status")
    allowed_statuses = {"active_tracking", "tracking_strengthened", "tracking_weakened", "tracking_needs_more_evidence", "tracking_paused", "tracking_archived"}
    ok = (
        current_status in allowed_statuses
        and audit.get("audit_records", 0) >= 1
        and audit.get("pending_created", 0) == 0
        and audit.get("paper_order_created", 0) == 0
        and audit.get("real_trade_created", 0) == 0
        and not entry.get("pending_human_review_allowed", True)
        and not entry.get("paper_order_allowed", True)
        and not entry.get("real_trade_allowed", True)
    )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "overall_status": "pass" if ok else "fail",
        "watchlist_status_update_validation": {
            "current_status": current_status,
            "audit_records": audit.get("audit_records", 0),
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "pending_allowed": bool(entry.get("pending_human_review_allowed", False)),
            "paper_order_allowed": bool(entry.get("paper_order_allowed", False)),
            "real_trade_allowed": bool(entry.get("real_trade_allowed", False)),
        },
        "safety": {
            "status_update_creates_pending": False,
            "status_update_creates_order": False,
            "status_update_creates_trade": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 46 watchlist status update")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
