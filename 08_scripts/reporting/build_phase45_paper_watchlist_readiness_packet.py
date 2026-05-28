#!/usr/bin/env python3
"""Build Phase 45 paper watchlist readiness packet."""

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
from smr_final_research_conclusion import build_final_research_conclusion
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    conclusion = build_final_research_conclusion(conn, ticker).get("final_research_conclusion") or {}
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "paper_watchlist_readiness_packet": {
            "readiness": conclusion.get("paper_watchlist_readiness") or "paper_watchlist_candidate",
            "tracking_goal": "monitor whether product mix/order visibility/shipment evidence continues to strengthen",
            "tracking_variables": [
                "product_mix",
                "order_visibility",
                "shipment",
                "ASP_price_proxy",
                "official_consensus",
                "supplier_share_scenario",
                "customer_allocation_proxy",
            ],
            "entry_boundary": {
                "paper_watchlist_allowed": True,
                "paper_order_allowed": False,
                "pending_human_review_allowed": False,
                "real_trade_allowed": False,
            },
            "tracking_questions": [
                "Does product mix continue to improve?",
                "Does order visibility become more concrete?",
                "Does any authorized consensus source become available?",
                "Does supplier share remain scenario-only?",
            ],
            "pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "watchlist_is_tracking_not_trade": True,
            "actual_watchlist_entry_created": False,
            "trade_recommendation_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("paper_watchlist_readiness_packet") or {}
    lines = [f"# Phase 45 Paper Watchlist Readiness Packet: {payload.get('ticker')}", "", f"- readiness: {body.get('readiness')}", f"- tracking_goal: {body.get('tracking_goal')}", ""]
    lines.extend(["## Tracking Variables"])
    lines.extend(f"- {item}" for item in body.get("tracking_variables") or [])
    lines.extend(["", "## Entry Boundary"])
    for key, value in (body.get("entry_boundary") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Tracking Questions"])
    lines.extend(f"- {item}" for item in body.get("tracking_questions") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 paper watchlist readiness packet")
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
