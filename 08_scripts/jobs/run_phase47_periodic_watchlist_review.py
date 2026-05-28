#!/usr/bin/env python3
"""Execute Phase 47 periodic watchlist review."""

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

from smr_agents import DB_PATH
from smr_new_evidence_delta_detector import build_new_evidence_delta
from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_paper_watchlist_periodic_review import upsert_periodic_review_state
from smr_periodic_review_audit import write_periodic_review_audit
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(
    conn: sqlite3.Connection,
    ticker: str,
    mode: str = "dry-run",
) -> dict:
    ticker = normalize_ticker(ticker)
    entry = get_paper_watchlist_entry(conn, ticker)
    before_wl_status = (entry or {}).get("watchlist_status") or "active_tracking"
    delta = build_new_evidence_delta(conn, ticker).get("new_evidence_delta") or {}
    new_evidence = delta.get("new_evidence_found", False)
    thesis_delta = "unchanged"
    after_wl_status = before_wl_status
    review_after = "review_completed"

    if mode == "execute":
        upsert_periodic_review_state(
            conn,
            ticker=ticker,
            review_status=review_after,
            review_cadence="weekly_or_on_new_evidence",
            thesis_delta=thesis_delta,
            new_evidence_found=new_evidence,
            metadata={"execution_mode": "periodic_review_phase47"},
        )
        write_periodic_review_audit(
            conn,
            ticker=ticker,
            action="periodic_watchlist_review",
            before_status=before_wl_status,
            after_status=after_wl_status,
            thesis_delta=thesis_delta,
            new_evidence_found=new_evidence,
        )
    review_before = "review_due"
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "periodic_review_execution": {
            "mode": mode,
            "review_status_before": review_before,
            "review_status_after": review_after if mode == "execute" else review_before,
            "watchlist_status_before": before_wl_status,
            "watchlist_status_after": after_wl_status,
            "thesis_delta": thesis_delta,
            "new_evidence_found": new_evidence,
            "audit_written": mode == "execute",
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
        "safety": {
            "executor_creates_pending": False,
            "executor_creates_order": False,
            "executor_creates_trade": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 47 periodic watchlist review")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute else "dry-run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker, mode=mode)
        if mode == "execute":
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
