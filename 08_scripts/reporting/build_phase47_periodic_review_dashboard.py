#!/usr/bin/env python3
"""Build Phase 47 periodic review dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[0]
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase46_thesis_strength_score import build_payload as build_score
from build_phase47_periodic_review_state import build_payload as build_state
from smr_agents import DB_PATH
from smr_paper_watchlist_entry import list_paper_watchlist_entries
from smr_periodic_review_audit import list_periodic_review_audits
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


TRACKING_FAMILY = {
    "active_tracking",
    "tracking_strengthened",
    "tracking_weakened",
    "tracking_needs_more_evidence",
}


def build_payload(conn: sqlite3.Connection) -> dict:
    entries = list_paper_watchlist_entries(conn)
    current_statuses = [e.get("watchlist_status") for e in entries]
    audits = list_periodic_review_audits(conn)
    reviews_completed = len(audits)
    rows = []
    for entry in entries:
        ticker = entry.get("ticker")
        score = build_score(ticker).get("thesis_strength_tracking") or {}
        state_payload = build_state(conn, ticker)
        review_state = state_payload.get("periodic_review_state") or {}
        rows.append({
            "ticker": ticker,
            "watchlist_status": entry.get("watchlist_status"),
            "review_status": review_state.get("review_status") or "review_due",
            "thesis_strength_score": score.get("thesis_strength_score", 62),
            "thesis_delta": review_state.get("thesis_delta", "unchanged"),
            "next_review": "weekly_or_on_new_evidence",
            "pending_allowed": False,
            "paper_order_allowed": False,
        })
    return {
        "generated_at": now_ts(),
        "summary": {
            "watchlist_entries": len(entries),
            "reviews_completed": reviews_completed,
            "tracking_strengthened": current_statuses.count("tracking_strengthened"),
            "tracking_weakened": current_statuses.count("tracking_weakened"),
            "tracking_unchanged": sum(
                1 for s in current_statuses if s in TRACKING_FAMILY and s != "tracking_strengthened" and s != "tracking_weakened"
            ),
            "new_evidence_found": 0,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
        "ticker_rows": rows,
        "safety": {
            "dashboard_creates_pending": False,
            "dashboard_creates_order": False,
            "dashboard_creates_trade": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 47 Periodic Review Dashboard",
        "",
        "## Summary",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Ticker Rows"])
    for row in payload.get("ticker_rows") or []:
        lines.append(
            f"- {row.get('ticker')}: {row.get('watchlist_status')} / "
            f"review={row.get('review_status')} / "
            f"score={row.get('thesis_strength_score')}"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 47 periodic review dashboard")
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
