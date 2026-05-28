#!/usr/bin/env python3
"""Build Phase 46 paper watchlist review packet."""

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

from build_phase46_paper_watchlist_entry import build_payload as build_entry
from build_phase46_thesis_strength_score import build_payload as build_score
from build_phase46_tracking_triggers import build_payload as build_triggers
from build_phase46_tracking_variables import build_payload as build_variables
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    entry = build_entry(conn, ticker).get("paper_watchlist_entry") or {}
    variables = build_variables(ticker).get("tracking_variables") or []
    triggers = build_triggers(ticker).get("tracking_triggers") or []
    score = build_score(ticker).get("thesis_strength_tracking") or {}
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "paper_watchlist_review_packet": {
            "watchlist_status": entry.get("watchlist_status") or "paper_watchlist_candidate",
            "source_conclusion": entry.get("source_conclusion_status") or "formal_research_conclusion_positive_watchlist",
            "tracking_variables": variables,
            "tracking_triggers": triggers,
            "thesis_strength_tracking": score,
            "why_tracking_not_pending": [
                "supplier_share remains scenario-only",
                "official_consensus remains unconfirmed",
                "customer_allocation remains proxy-only",
                "valuation boundary remains scenario analysis",
            ],
            "next_tracking_questions": [
                "Does product mix continue to strengthen?",
                "Does order visibility become more concrete?",
                "Does authorized consensus source become available?",
            ],
            "forbidden_actions": [
                "create_pending",
                "create_paper_order",
                "create_trade",
            ],
        },
        "safety": {
            "watchlist_packet_is_investment_order": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    packet = payload.get("paper_watchlist_review_packet") or {}
    score = packet.get("thesis_strength_tracking") or {}
    lines = [
        f"# Phase 46 Paper Watchlist Review Packet: {payload.get('ticker')}",
        "",
        "## Watchlist Status",
        f"- watchlist_status: {packet.get('watchlist_status')}",
        "",
        "## Source Research Conclusion",
        f"- source_conclusion: {packet.get('source_conclusion')}",
        "",
        "## Tracking Variables",
    ]
    for row in packet.get("tracking_variables") or []:
        lines.append(f"- {row.get('variable')}: {row.get('current_status')}")
    lines.extend(["", "## Tracking Triggers"])
    for row in packet.get("tracking_triggers") or []:
        lines.append(f"- {row.get('trigger_type')}: {row.get('variable')} -> {row.get('resulting_status')}")
    lines.extend(
        [
            "",
            "## Thesis Strength Score",
            f"- score: {score.get('thesis_strength_score')}",
            f"- bucket: {score.get('thesis_strength_bucket')}",
            "",
            "## Why Tracking, Not Pending",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("why_tracking_not_pending") or [])
    lines.extend(["", "## Next Tracking Questions"])
    lines.extend(f"- {item}" for item in packet.get("next_tracking_questions") or [])
    lines.extend(["", "## Forbidden Actions"])
    lines.extend(f"- {item}" for item in packet.get("forbidden_actions") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 46 paper watchlist review packet")
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
