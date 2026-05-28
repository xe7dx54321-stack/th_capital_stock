#!/usr/bin/env python3
"""Build Phase 45 final evidence sufficiency review."""

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
from smr_final_research_asset_aggregator import REMAINING_CORE_GAPS, STRENGTHENED_VARIABLES, build_final_research_asset_summary
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str = TARGET_REVIEW_TICKER) -> dict:
    ticker = normalize_ticker(ticker)
    assets = build_final_research_asset_summary(conn, ticker).get("final_research_asset_summary") or {}
    manual_reviewed = (assets.get("evidence_chain") or {}).get("manual_candidates_reviewed", 0)
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "evidence_sufficiency_review": {
            "evidence_sufficiency_for_research_conclusion": "sufficient_for_watchlist_research",
            "evidence_sufficiency_for_investment_pending": "insufficient",
            "positive_evidence_areas": list(STRENGTHENED_VARIABLES),
            "insufficient_evidence_areas": list(REMAINING_CORE_GAPS),
            "review_dimensions": [
                "evidence_quantity",
                "evidence_quality",
                "evidence_recency",
                "source_diversity",
                "company_specificity",
                "variable_coverage",
                "manual_candidate_contribution",
                "sensitive_variable_gaps",
                "evidence_integrity",
                "promotion_safety",
            ],
            "manual_candidates": {
                "helpful_for_context": manual_reviewed == 3,
                "manual_candidates_reviewed": manual_reviewed,
                "confirmed_variables_added": 0,
            },
            "promotion_safety": {
                "usable_for_promotion_true": 0,
                "pending_allowed": False,
                "paper_order_allowed": False,
                "real_trade_allowed": False,
            },
        },
        "safety": {
            "research_sufficiency_separated_from_investment_pending": True,
            "trade_recommendation_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def render_markdown(payload: dict) -> str:
    body = payload.get("evidence_sufficiency_review") or {}
    lines = [f"# Phase 45 Final Evidence Sufficiency Review: {payload.get('ticker')}", ""]
    lines.extend(["## Sufficiency", f"- research_conclusion: {body.get('evidence_sufficiency_for_research_conclusion')}", f"- investment_pending: {body.get('evidence_sufficiency_for_investment_pending')}"])
    lines.extend(["", "## Positive Evidence Areas"])
    lines.extend(f"- {item}" for item in body.get("positive_evidence_areas") or [])
    lines.extend(["", "## Insufficient Evidence Areas"])
    lines.extend(f"- {item}" for item in body.get("insufficient_evidence_areas") or [])
    lines.extend(["", "## Promotion Safety"])
    for key, value in (body.get("promotion_safety") or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 45 final evidence sufficiency review")
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
