#!/usr/bin/env python3
"""Build Phase 47 periodic review packet."""

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

from build_phase47_periodic_review_state import build_payload as build_state
from build_phase47_tracking_variable_snapshot import build_payload as build_snapshot
from build_phase47_new_evidence_delta import build_payload as build_delta
from build_phase47_thesis_strength_update import build_payload as build_score
from smr_agents import DB_PATH
from smr_paper_watchlist_entry import get_paper_watchlist_entry
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    entry = get_paper_watchlist_entry(conn, ticker)
    wl_status = (entry or {}).get("watchlist_status") or "tracking_strengthened"
    state = build_state(conn, ticker)
    snapshot = build_snapshot(ticker)
    delta = build_delta(conn, ticker)
    score = build_score(ticker)
    review_status = (state.get("periodic_review_state") or {}).get("review_status") or "review_completed"
    snapshot_data = snapshot.get("tracking_variable_snapshot") or {}
    delta_data = delta.get("new_evidence_delta") or {}
    score_data = score.get("thesis_strength_update") or {}
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "periodic_review_packet": {
            "watchlist_status": wl_status,
            "review_status": review_status,
            "tracking_variable_snapshot": snapshot_data,
            "new_evidence_delta": delta_data,
            "new_evidence_revalidation": {
                "overall_status": "no_new_evidence_noop",
            },
            "thesis_strength_update": score_data,
            "review_judgment": {
                "thesis_delta": "unchanged",
                "continue_tracking": True,
                "needs_more_evidence": True,
                "archive_candidate": False,
            },
            "why_not_pending": [
                "official consensus remains unconfirmed",
                "supplier share remains scenario-only",
                "customer allocation remains proxy-only",
                "valuation remains scenario-bound",
            ],
            "forbidden_actions": [
                "create_pending",
                "create_paper_order",
                "create_trade",
            ],
        },
        "safety": {
            "packet_strengthened_is_buy": False,
            "packet_creates_pending": False,
            "packet_creates_order": False,
            "packet_creates_trade": False,
        },
    }


def render_markdown(payload: dict) -> str:
    packet = payload.get("periodic_review_packet") or {}
    judgment = packet.get("review_judgment") or {}
    lines = [
        f"# Phase 47 Periodic Review Packet: {payload.get('ticker')}",
        "",
        "## Review Status",
        f"- watchlist_status: {packet.get('watchlist_status')}",
        f"- review_status: {packet.get('review_status')}",
        "",
        "## Review Judgment",
        f"- thesis_delta: {judgment.get('thesis_delta')}",
        f"- continue_tracking: {judgment.get('continue_tracking')}",
        f"- needs_more_evidence: {judgment.get('needs_more_evidence')}",
        f"- archive_candidate: {judgment.get('archive_candidate')}",
        "",
        "## Why Not Pending",
    ]
    for reason in packet.get("why_not_pending") or []:
        lines.append(f"- {reason}")
    lines.extend(["", "## Forbidden Actions"])
    for action in packet.get("forbidden_actions") or []:
        lines.append(f"- {action}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 47 periodic review packet")
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
