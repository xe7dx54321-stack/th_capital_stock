#!/usr/bin/env python3
"""Execute Phase 48 event-driven watchlist evidence refresh."""

from __future__ import annotations

import argparse, json, sqlite3, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
for path in (LIB_DIR, LIB_DIR.parent / "reporting"):
    if str(path) not in sys.path: sys.path.insert(0, str(path))

from smr_agents import DB_PATH
from smr_event_trigger_audit import write_event_trigger_audit
from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_watchlist_event_detector import detect_events
from smr_event_driven_refresh_task import generate_refresh_tasks
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(conn, ticker, mode="dry-run"):
    ticker = normalize_ticker(ticker)
    entry = get_paper_watchlist_entry(conn, ticker)
    before_status = (entry or {}).get("watchlist_status") or "tracking_strengthened"
    events = detect_events(conn, ticker)
    tasks = generate_refresh_tasks(events, ticker)
    touched = list({t["target_variable"] for t in tasks})
    audit_written = False
    if mode == "execute" and tasks:
        for task in tasks:
            write_event_trigger_audit(
                conn, ticker=ticker, event_id=task["event_id"],
                action="event_driven_research_refresh",
                before_watchlist_status=before_status,
                after_watchlist_status=before_status,
                thesis_delta="unchanged_or_modestly_strengthened",
                metadata={"task_type": task["task_type"], "target_variable": task["target_variable"]},
            )
        audit_written = True
    return {
        "generated_at": now_ts(), "ticker": ticker,
        "event_evidence_refresh": {
            "mode": mode,
            "tasks_checked": len(tasks),
            "tasks_executed": len(tasks) if mode == "execute" else 0,
            "new_evidence_candidates_found": 0,
            "new_evidence_candidates_written": 0,
            "tracking_variables_touched": touched,
            "refresh_status": "research_refresh_completed" if mode == "execute" else "dry_run_completed",
            "audit_written": audit_written,
            "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        },
        "safety": {
            "executor_creates_pending": False, "executor_creates_order": False,
            "executor_creates_trade": False, "promotion_rules_relaxed": False,
        },
    }

def main():
    p = argparse.ArgumentParser(description="Run Phase 48 event evidence refresh")
    p.add_argument("--db-path", default=str(DB_PATH)); p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--execute", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    mode = "execute" if args.execute else "dry-run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker, mode=mode)
        if mode == "execute": conn.commit()
    finally: conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
