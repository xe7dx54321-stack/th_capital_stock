#!/usr/bin/env python3
"""Upsert a Phase 46 paper watchlist entry."""

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
from smr_paper_watchlist_entry import build_paper_watchlist_entry, get_paper_watchlist_entry, upsert_paper_watchlist_entry
from smr_paper_watchlist_lifecycle import validate_watchlist_transition
from smr_registry import register_snapshot
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "upsert_phase46_paper_watchlist_entry.py"


def _dry_run_result(conn: sqlite3.Connection, ticker: str) -> dict:
    existing = get_paper_watchlist_entry(conn, ticker)
    before_status = (existing or {}).get("watchlist_status") or "paper_watchlist_candidate"
    after_status = before_status if existing and before_status != "paper_watchlist_candidate" else "active_tracking"
    ok, reason = validate_watchlist_transition(before_status, after_status)
    entry = existing or build_paper_watchlist_entry(conn, ticker, status="paper_watchlist_candidate")
    return {
        "entry": entry,
        "before_status": before_status,
        "after_status": after_status,
        "transition_allowed": ok,
        "transition_validation_reason": reason,
        "entry_created": existing is None,
        "entry_updated": existing is not None and before_status != after_status,
        "duplicate_skipped": existing is not None and before_status == after_status,
    }


def build_payload(conn: sqlite3.Connection, *, ticker: str, mode: str = "dry_run") -> dict:
    ticker = normalize_ticker(ticker)
    if mode == "execute":
        result = upsert_paper_watchlist_entry(
            conn,
            ticker=ticker,
            status="active_tracking",
            metadata={"source_job": SCRIPT_NAME, "mode": mode},
        )
        audit = write_paper_watchlist_audit(
            conn,
            ticker=ticker,
            action="create_watchlist_entry" if result.get("entry_created") else "upsert_watchlist_entry",
            before_status=result.get("before_status") or "paper_watchlist_candidate",
            after_status=result.get("watchlist_status") or "active_tracking",
            metadata={"watchlist_entry_id": result.get("watchlist_entry_id"), "duplicate_skipped": result.get("duplicate_skipped")},
        )
        audit_written = bool(audit.get("audit_id"))
        entry = result
    else:
        result = _dry_run_result(conn, ticker)
        audit_written = False
        entry = result.get("entry") or {}

    body = {
        "mode": mode,
        "entry_created": bool(result.get("entry_created")),
        "entry_updated": bool(result.get("entry_updated")),
        "duplicate_skipped": bool(result.get("duplicate_skipped")),
        "watchlist_status": result.get("after_status") or entry.get("watchlist_status"),
        "tracking_mode": entry.get("tracking_mode") or "research_only_tracking",
        "audit_written": audit_written,
        "pending_created": 0,
        "paper_order_created": 0,
        "real_trade_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "watchlist_upsert_result": body,
        "paper_watchlist_entry": entry,
        "safety": {
            "watchlist_entry_is_pending": False,
            "watchlist_entry_is_paper_position": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upsert Phase 46 paper watchlist entry")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, mode=mode)
        if mode == "execute":
            conn.commit()
            body = payload.get("watchlist_upsert_result") or {}
            register_snapshot(
                conn,
                "phase46_paper_watchlist_entry",
                normalize_ticker(args.ticker),
                body.get("watchlist_status") or "active_tracking",
                SCRIPT_NAME,
                payload=payload,
            )
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
