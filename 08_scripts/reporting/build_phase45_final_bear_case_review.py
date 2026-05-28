#!/usr/bin/env python3
"""Build Phase 45 final bear case review."""

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
        "final_bear_case_review": {
            "bear_case_status": "partially_mitigated_but_not_cleared",
            "residual_risk_level": "medium",
            "original_bear_case": [
                "AI optical module cycle strength may not translate into company-specific upside",
                "customer/order allocation could remain opaque",
                "valuation sensitivity remains high without a confirmed benchmark",
            ],
            "mitigating_evidence": [
                "product mix evidence",
                "order visibility evidence",
                "shipment evidence",
            ],
            "evidence_that_does_not_mitigate": [
                "supplier share scenario assumption",
                "official consensus candidate",
                "customer allocation proxy",
            ],
            "remaining_bear_points": [
                "supplier share unconfirmed",
                "official consensus missing",
                "customer allocation unconfirmed",
                "scenario dependence high",
            ],
            "impact_on_research_conclusion": "does_not_block_watchlist_research",
            "impact_on_pending": "blocks_investment_pending",
            "pending_created": 0,
        },
        "safety": {
            "bear_case_cleared": False,
            "trade_recommendation_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("final_bear_case_review") or {}
    lines = [f"# Phase 45 Final Bear Case Review: {payload.get('ticker')}", ""]
    lines.extend(["## Status", f"- bear_case_status: {body.get('bear_case_status')}", f"- residual_risk_level: {body.get('residual_risk_level')}"])
    for section in ("mitigating_evidence", "evidence_that_does_not_mitigate", "remaining_bear_points"):
        lines.extend(["", f"## {section}"])
        lines.extend(f"- {item}" for item in body.get(section) or [])
    lines.extend(["", "## Impact", f"- research_conclusion: {body.get('impact_on_research_conclusion')}", f"- pending: {body.get('impact_on_pending')}"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final bear case review")
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
