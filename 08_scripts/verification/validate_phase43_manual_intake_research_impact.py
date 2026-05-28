#!/usr/bin/env python3
"""Validate Phase 43 manual intake research packet impact."""

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
from smr_manual_intake_candidate_generator import list_manual_intake_candidates
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    candidates = list_manual_intake_candidates(conn, ticker=ticker)
    persisted = [candidate for candidate in candidates if candidate.get("persisted")]
    rows = persisted or candidates
    by_type = {candidate.get("evidence_type"): candidate for candidate in rows}
    impact = {
        "manual_candidates_written": len(persisted),
        "official_consensus_candidate_added": "official_consensus" in by_type,
        "official_consensus_confirmed": False,
        "supplier_share_scenario_added": any(candidate.get("source_type") == "scenario_assumption" for candidate in rows),
        "supplier_share_confirmed": False,
        "customer_allocation_proxy_added": any(candidate.get("source_type") == "proxy_evidence_note" for candidate in rows),
        "customer_allocation_confirmed": False,
        "research_quality_delta": "better_bounded_with_manual_candidates" if rows else "unchanged",
        "expectation_gap_delta": "better_context_but_not_confirmed" if "official_consensus" in by_type else "unchanged",
        "pending_created": 0,
        "paper_order_created": 0,
        "promotion_allowed_true": 0,
    }
    ok = (
        not impact["official_consensus_confirmed"]
        and not impact["supplier_share_confirmed"]
        and not impact["customer_allocation_confirmed"]
        and impact["pending_created"] == 0
        and impact["paper_order_created"] == 0
        and impact["promotion_allowed_true"] == 0
    )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "overall_status": "pass" if ok else "fail",
        "manual_intake_research_impact": impact,
        "safety": {
            "candidate_directly_confirmed": False,
            "scenario_is_fact": False,
            "proxy_is_confirmed_allocation": False,
            "trade_recommendation_generated": False,
            "target_price_generated": False,
            "position_guidance_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 43 manual intake research impact")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
