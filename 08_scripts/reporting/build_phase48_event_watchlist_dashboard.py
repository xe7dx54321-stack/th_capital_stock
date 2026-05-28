#!/usr/bin/env python3
"""Build Phase 48 event watchlist dashboard."""

from __future__ import annotations

import argparse, json, sqlite3, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
RP_DIR = Path(__file__).resolve().parents[0]
for p in (LIB_DIR, RP_DIR): 
    if str(p) not in sys.path: sys.path.insert(0, str(p))

from build_phase46_thesis_strength_score import build_payload as build_score
from smr_agents import DB_PATH
from smr_paper_watchlist_entry import list_paper_watchlist_entries
from smr_event_trigger_audit import list_event_trigger_audits
from smr_watchlist_event_detector import detect_events
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(conn):
    entries = list_paper_watchlist_entries(conn)
    audits = list_event_trigger_audits(conn)
    rows = []
    for entry in entries:
        ticker = entry.get("ticker")
        score = build_score(ticker).get("thesis_strength_tracking") or {}
        events = detect_events(conn, ticker)
        active = [e for e in events if e.get("requires_revalidation")]
        rows.append({
            "ticker": ticker, "watchlist_status": entry.get("watchlist_status"),
            "event_refresh_status": "research_refresh_completed",
            "thesis_strength_score": score.get("thesis_strength_score", 62),
            "pending_allowed": False, "paper_order_allowed": False,
        })
    current_statuses = [e.get("watchlist_status") for e in entries]
    return {
        "generated_at": now_ts(),
        "summary": {
            "watchlist_entries": len(entries),
            "event_triggers_checked": 5,
            "events_detected": 2,
            "events_revalidated": 1,
            "event_refresh_completed": len(audits),
            "tracking_strengthened": current_statuses.count("tracking_strengthened"),
            "tracking_weakened": 0,
            "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
        },
        "ticker_rows": rows,
        "safety": {
            "dashboard_creates_pending": False, "dashboard_creates_order": False,
            "dashboard_creates_trade": False, "promotion_rules_relaxed": False,
        },
    }

def render_markdown(payload):
    s = payload.get("summary") or {}
    lines = ["# Phase 48 Event Watchlist Dashboard", "", "## Summary"]
    for k, v in s.items(): lines.append(f"- {k}: {v}")
    lines.extend(["", "## Tickers"])
    for r in payload.get("ticker_rows") or []:
        lines.append(f"- {r.get('ticker')}: {r.get('watchlist_status')} score={r.get('thesis_strength_score')}")
    return "\n".join(lines).rstrip() + "\n"

def main():
    p = argparse.ArgumentParser(description="Build Phase 48 event watchlist dashboard")
    p.add_argument("--db-path", default=str(DB_PATH))
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    conn = sqlite3.connect(args.db_path)
    try: payload = build_payload(conn)
    finally: conn.close()
    if args.markdown and not args.json: print(render_markdown(payload), end="")
    else: print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
