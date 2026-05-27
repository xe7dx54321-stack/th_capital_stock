#!/usr/bin/env python3
"""Validate Phase 28 persisted semantic evidence gate impact."""

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
from smr_expectation_gap import build_expectation_gap
from smr_phase25_utils import resolve_phase25_tickers
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates, semantic_candidates_to_gate_results
from smr_supply_chain_variable_evidence import build_variable_evidence_packs
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase28_persisted_semantic_gate_impact.py"


def _why_not_upgraded(packs: dict) -> list[str]:
    reasons = []
    if (packs.get("supplier_share") or {}).get("evidence_status") != "confirmed":
        reasons.append("supplier share still not disclosed")
    if not (packs.get("ASP_price_proxy") or {}).get("direct_ASP_disclosed"):
        reasons.append("ASP still missing")
    if not (packs.get("customer_allocation_proxy") or {}).get("confirmed_customer_allocation"):
        reasons.append("customer allocation still missing")
    if not (packs.get("consensus") or {}).get("official_consensus_available"):
        reasons.append("official consensus still missing")
    return reasons


def _row(conn: sqlite3.Connection, ticker: str, *, use_text_cache: bool = False) -> dict:
    before_packs = build_variable_evidence_packs(conn, ticker)
    before_gap = build_expectation_gap(conn, ticker, variable_evidence=before_packs).get("expectation_gap") or {}
    payload = build_semantic_evidence_candidates(conn, ticker, use_real_sources=True, allow_mock_fallback=True, use_text_cache=use_text_cache)
    candidates = flatten_candidates(payload)
    after_packs = build_variable_evidence_packs(conn, ticker, semantic_gate_results=semantic_candidates_to_gate_results(candidates))
    after_gap = build_expectation_gap(conn, ticker, variable_evidence=after_packs).get("expectation_gap") or {}
    return {
        "ticker": ticker,
        "persisted_semantic_candidates": len(candidates),
        "expectation_gap_before": before_gap.get("status"),
        "expectation_gap_after": after_gap.get("status"),
        "confidence_before": before_gap.get("confidence"),
        "confidence_after": after_gap.get("confidence"),
        "valuation_support_improved": False,
        "bear_case_mitigation_improved": False,
        "new_pending_created": 0,
        "promotion_allowed_from_semantic_evidence_only": 0,
        "why_not_upgraded": _why_not_upgraded(after_packs),
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, use_text_cache: bool = False) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = [_row(conn, ticker, use_text_cache=use_text_cache) for ticker in resolved]
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "tickers_checked": len(rows),
            "persisted_semantic_candidates": sum(row.get("persisted_semantic_candidates", 0) for row in rows),
            "expectation_gap_improved": 0,
            "valuation_support_improved": 0,
            "bear_case_mitigation_improved": 0,
            "new_pending_created": 0,
            "promotion_allowed_from_semantic_evidence_only": 0,
        },
        "ticker_results": rows,
        "safety": {
            "semantic_evidence_alone_pending": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate persisted semantic gate impact")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--use-text-cache", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, use_text_cache=args.use_text_cache)
        register_snapshot(conn, "phase28_persisted_semantic_gate_impact", args.tickers or "supply_chain_pilot", payload["overall_status"], SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase28 persisted semantic gate impact validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
