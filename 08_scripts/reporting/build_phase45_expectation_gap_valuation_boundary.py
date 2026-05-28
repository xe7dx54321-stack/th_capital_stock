#!/usr/bin/env python3
"""Build Phase 45 expectation gap and valuation boundary review."""

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
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    del conn
    ticker = normalize_ticker(ticker)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "expectation_gap_valuation_boundary": {
            "expectation_gap_status": "potential_positive_gap_but_unconfirmed",
            "expectation_gap_confidence": "medium_low",
            "expectation_benchmark_quality": "candidate_context_only",
            "official_consensus_confirmed": False,
            "internal_proxy_usage": "context_only",
            "valuation_support_status": "partial",
            "valuation_boundary": "scenario_analysis_only",
            "valuation_blockers": [
                "official consensus not confirmed",
                "supplier share scenario only",
                "customer allocation proxy only",
            ],
            "why_not_stronger": [
                "official consensus not confirmed",
                "supplier share scenario only",
                "customer allocation proxy only",
            ],
            "investment_pending_allowed": False,
            "pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "high_confidence_expectation_gap_claimed": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("expectation_gap_valuation_boundary") or {}
    lines = [f"# Phase 45 Expectation Gap & Valuation Boundary: {payload.get('ticker')}", ""]
    for key in ("expectation_gap_status", "expectation_gap_confidence", "official_consensus_confirmed", "internal_proxy_usage", "valuation_support_status", "valuation_boundary", "investment_pending_allowed"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Why Not Stronger"])
    lines.extend(f"- {item}" for item in body.get("why_not_stronger") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 expectation gap and valuation boundary review")
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
