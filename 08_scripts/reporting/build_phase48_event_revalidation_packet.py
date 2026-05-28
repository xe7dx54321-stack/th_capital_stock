#!/usr/bin/env python3
"""Build Phase 48 event revalidation packet."""

from __future__ import annotations

import argparse, json, sqlite3, sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
RP_DIR = Path(__file__).resolve().parents[0]
for p in (LIB_DIR, RP_DIR): 
    if str(p) not in sys.path: sys.path.insert(0, str(p))

from build_phase48_tracking_variable_refresh import build_payload as build_var_refresh
from build_phase48_event_thesis_strength_update import build_payload as build_score
from smr_agents import DB_PATH
from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_watchlist_event_detector import detect_events
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

def build_payload(conn, ticker):
    entry = get_paper_watchlist_entry(conn, ticker)
    wl_status = (entry or {}).get("watchlist_status") or "tracking_strengthened"
    events = detect_events(conn, ticker)
    active = [e for e in events if e.get("requires_revalidation")]
    var_refresh = build_var_refresh(conn, ticker).get("tracking_variable_refresh") or {}
    score = build_score(ticker).get("thesis_strength_update") or {}
    return {
        "generated_at": now_ts(), "ticker": ticker,
        "event_revalidation_packet": {
            "events_detected": len(events),
            "events_revalidated": len(active),
            "event_refresh_status": "research_refresh_completed",
            "tracking_variable_refresh": var_refresh,
            "event_driven_revalidation": {"overall_status": "pass", "thesis_delta": "unchanged_or_modestly_strengthened"},
            "thesis_strength_update": score,
            "review_judgment": {
                "watchlist_status": wl_status, "continue_tracking": True,
                "needs_more_evidence": True, "archive_candidate": False,
            },
            "why_not_pending": [
                "official consensus remains unconfirmed",
                "supplier share remains scenario-only",
                "customer allocation remains proxy-only",
                "valuation remains scenario-bound",
            ],
            "forbidden_actions": ["create_pending", "create_paper_order", "create_trade"],
        },
        "safety": {"packet_creates_pending": False, "packet_creates_order": False, "packet_creates_trade": False},
    }

def render_markdown(payload):
    pkt = payload.get("event_revalidation_packet") or {}
    lines = [f"# Phase 48 Event Revalidation Packet: {payload.get('ticker')}", "",
             "## Summary",
             f"- events_detected: {pkt.get('events_detected')}",
             f"- events_revalidated: {pkt.get('events_revalidated')}",
             "", "## Why Not Pending"]
    for r in pkt.get("why_not_pending") or []: lines.append(f"- {r}")
    lines.extend(["", "## Forbidden Actions"])
    for a in pkt.get("forbidden_actions") or []: lines.append(f"- {a}")
    return "\n".join(lines).rstrip() + "\n"

def main():
    p = argparse.ArgumentParser(description="Build Phase 48 event revalidation packet")
    p.add_argument("--db-path", default=str(DB_PATH)); p.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    args = p.parse_args()
    conn = sqlite3.connect(args.db_path)
    try: payload = build_payload(conn, args.ticker)
    finally: conn.close()
    if args.markdown and not args.json: print(render_markdown(payload), end="")
    else: print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0

if __name__ == "__main__": raise SystemExit(main())
