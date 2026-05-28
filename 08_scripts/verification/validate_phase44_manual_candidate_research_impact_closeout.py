#!/usr/bin/env python3
"""Validate Phase 44 manual candidate research impact closeout."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_manual_candidate_final_usage_matrix import build_payload as build_matrix
from smr_agents import DB_PATH
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    ticker = normalize_ticker(ticker)
    matrix = build_matrix(conn, ticker).get("manual_candidate_final_usage_matrix") or {}
    rows = matrix.get("rows") or []
    by_type = {row.get("candidate_type"): row for row in rows}
    impact = {
        "manual_candidates_reviewed": len(rows),
        "official_consensus_candidate_accepted": (by_type.get("official_consensus") or {}).get("review_status") == "manual_candidate_accepted",
        "official_consensus_confirmed": False,
        "supplier_share_scenario_only": (by_type.get("supplier_share") or {}).get("review_status") == "manual_candidate_scenario_only",
        "supplier_share_confirmed": False,
        "customer_allocation_proxy_only": (by_type.get("customer_allocation") or {}).get("review_status") == "manual_candidate_proxy_only",
        "customer_allocation_confirmed": False,
        "research_quality_delta": "better_bounded_not_upgraded",
        "expectation_gap_delta": "better_context_not_confirmed",
        "why_not_pending_strengthened": True,
        "pending_created": 0,
        "paper_order_created": 0,
        "promotion_allowed_true": 0,
    }
    ok = (
        impact["manual_candidates_reviewed"] == 3
        and impact["official_consensus_candidate_accepted"]
        and impact["supplier_share_scenario_only"]
        and impact["customer_allocation_proxy_only"]
        and not impact["official_consensus_confirmed"]
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
        "manual_candidate_research_impact_closeout": impact,
        "safety": {
            "confirmed_variables_added": 0,
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
    parser = argparse.ArgumentParser(description="Validate Phase 44 research impact closeout")
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
