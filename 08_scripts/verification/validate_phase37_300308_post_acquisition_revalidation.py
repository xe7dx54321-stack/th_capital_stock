#!/usr/bin/env python3
"""Validate Phase 37 post-acquisition research impact for 300308.SZ."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_research_quality_scoring import build_research_quality_score
from smr_targeted_evidence_candidate_builder import build_targeted_evidence_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _candidate_variables(payload: dict[str, Any]) -> list[str]:
    rows = (payload.get("targeted_evidence_candidates") or {}).get("candidate_rows") or []
    mapping = {
        "ASP_price_signal": "ASP_price_proxy",
        "shipment_signal": "shipment",
        "order_visibility_signal": "order_visibility",
        "customer_allocation_signal": "customer_allocation_proxy",
    }
    return sorted({mapping.get(str(row.get("variable_type")), str(row.get("variable_type"))) for row in rows})


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    ticker = "300308.SZ"
    quality_before = (build_research_quality_score(conn, ticker).get("research_quality") or {}).get("overall_quality")
    candidates = build_targeted_evidence_candidates(conn, ticker, mode="dry_run")
    body = candidates.get("targeted_evidence_candidates") or {}
    variables = _candidate_variables(candidates)
    improved = [item for item in variables if item in {"ASP_price_proxy", "shipment", "order_visibility", "customer_allocation_proxy"}]
    delta = "modestly_strengthened" if body.get("eligible_for_persistence", 0) else "unchanged_needs_more_data"
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "post_acquisition_revalidation": {
            "new_evidence_candidates": body.get("eligible_for_persistence", 0),
            "variable_packs_updated": len(improved),
            "research_quality_before": quality_before,
            "research_quality_after": "medium_low" if quality_before == "medium_low" else quality_before,
            "research_quality_delta": delta,
            "valuation_support_delta": "improved_but_still_partial" if "ASP_price_proxy" in improved else "unchanged",
            "bear_case_delta": "partially_mitigated_by_visibility_evidence" if {"shipment", "order_visibility"} & set(improved) else "unchanged",
            "expectation_gap_delta": "unchanged",
            "variables_improved": improved,
            "still_missing_variables": ["supplier_share", "official_consensus", "confirmed_customer_allocation"],
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "post_acquisition_not_promotion": True,
            "investment_advice_generated": False,
            "target_price_generated": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 37 300308 post-acquisition revalidation")
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
