#!/usr/bin/env python3
"""Update Phase 46 paper watchlist status."""

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
from smr_paper_watchlist_audit import write_paper_watchlist_audit
from smr_paper_watchlist_entry import get_paper_watchlist_entry, upsert_paper_watchlist_entry
from smr_paper_watchlist_lifecycle import FORBIDDEN_STATUSES, validate_watchlist_transition
from smr_registry import register_snapshot
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "update_phase46_watchlist_status.py"


def build_payload(conn: sqlite3.Connection, *, ticker: str, status: str, mode: str = "dry_run") -> dict:
    ticker = normalize_ticker(ticker)
    existing = get_paper_watchlist_entry(conn, ticker)
    before_status = (existing or {}).get("watchlist_status") or "paper_watchlist_candidate"
    ok, reason = validate_watchlist_transition(before_status, status)
    if status in FORBIDDEN_STATUSES:
        ok = False
    audit_written = False
    after_status = status
    if mode == "execute" and ok:
        updated = upsert_paper_watchlist_entry(
            conn,
            ticker=ticker,
            status=status,
            metadata={"source_job": SCRIPT_NAME, "status_update_requested": status},
        )
        after_status = updated.get("watchlist_status") or status
        audit = write_paper_watchlist_audit(
            conn,
            ticker=ticker,
            action="update_watchlist_status",
            before_status=before_status,
            after_status=after_status,
            metadata={"requested_status": status, "watchlist_entry_id": updated.get("watchlist_entry_id")},
        )
        audit_written = bool(audit.get("audit_id"))
    body = {
        "mode": mode,
        "before_status": before_status,
        "after_status": after_status,
        "transition_allowed": ok,
        "transition_validation_reason": reason,
        "audit_written": audit_written,
        "pending_created": 0,
        "paper_order_created": 0,
        "real_trade_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "watchlist_status_update": body,
        "safety": {
            "tracking_strengthened_is_pending": False,
            "tracking_weakened_is_trade_recommendation": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Phase 46 paper watchlist status")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--status", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, status=args.status, mode=mode)
        body = payload.get("watchlist_status_update") or {}
        if mode == "execute" and body.get("transition_allowed"):
            conn.commit()
            register_snapshot(
                conn,
                "phase46_paper_watchlist_status",
                normalize_ticker(args.ticker),
                body.get("after_status") or args.status,
                SCRIPT_NAME,
                payload=payload,
            )
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if (payload.get("watchlist_status_update") or {}).get("transition_allowed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
