#!/usr/bin/env python3
"""Validate Phase 38 300308 research packet after candidate persistence."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_evidence_chain_refresh import build_payload as build_chain_refresh
from smr_agents import DB_PATH
from smr_research_quality_scoring import build_research_quality_score
from smr_targeted_candidate_inventory import TARGET_TICKER
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    quality = (build_research_quality_score(conn, TARGET_TICKER).get("research_quality") or {}).get("overall_quality")
    refresh = build_chain_refresh(conn).get("evidence_chain_refresh") or {}
    new_written = int(refresh.get("new_candidates_written") or 0)
    variables = sorted((refresh.get("new_evidence_by_variable") or {}).keys())
    delta = "strengthened_with_new_supporting_evidence" if new_written else "unchanged_no_persistence_yet"
    return {
        "generated_at": now_ts(),
        "ticker": TARGET_TICKER,
        "research_packet_post_persistence": {
            "research_quality_before": "medium_low",
            "research_quality_after": quality or "medium_low",
            "quality_delta": delta,
            "evidence_coverage_delta": "improved" if new_written else "unchanged",
            "valuation_support_delta": "improved_but_partial" if {"ASP_price_proxy", "product_mix"} & set(variables) else "unchanged",
            "bear_case_delta": "partially_mitigated" if {"shipment", "order_visibility"} & set(variables) else "unchanged",
            "expectation_gap_delta": "unchanged",
            "variables_improved": variables,
            "still_missing": ["supplier_share", "official_consensus", "confirmed_customer_allocation"],
            "promotion_allowed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "post_persistence_not_promotion": True,
            "customer_allocation_proxy_confirmed": False,
            "investment_advice_generated": False,
            "target_price_generated": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 38 300308 post-persistence research packet")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
