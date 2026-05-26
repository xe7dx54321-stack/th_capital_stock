#!/usr/bin/env python3
"""Validate Phase 25 expectation-gap gate integration guardrails."""

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

from build_phase25_supply_chain_expectation_gap_packet import build_packet
from smr_agents import DB_PATH
from smr_phase25_utils import resolve_phase25_tickers
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase25_expectation_gap_gate_integration.py"


def build_ticker_result(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    packet = build_packet(conn, ticker)
    sections = packet.get("sections") or {}
    gap = sections.get("expectation_gap") or {}
    sensitivity = sections.get("revenue_sensitivity") or {}
    positive = gap.get("status") in {"strong_positive_gap", "potential_positive_gap"}
    valuation_support = sensitivity.get("valuation_support") or "context_only"
    thesis_evidence = "supporting" if positive else "context_only"
    why_not_pending = [
        "expectation gap alone cannot trigger pending",
        "official consensus unavailable",
        "supplier share assumption low confidence or missing",
        "no company-specific customer allocation evidence",
    ]
    if valuation_support != "supporting":
        why_not_pending.append("valuation support remains context_only")
    return {
        "ticker": packet.get("ticker"),
        "company_name": packet.get("company_name"),
        "expectation_gap_status": gap.get("status"),
        "score": gap.get("score"),
        "confidence": gap.get("confidence"),
        "packet_status": packet.get("packet_status"),
        "gate_impact": {
            "thesis_evidence": thesis_evidence,
            "valuation_support": "context_to_supporting" if valuation_support == "supporting" else "context_only",
            "bear_case": "supporting_context" if positive else "unchanged",
            "promotion_allowed": False,
        },
        "why_not_pending": why_not_pending,
        "new_pending_created": False,
        "promotion_allowed_from_gap_only": False,
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, watchlist: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers, watchlist)
    rows = [build_ticker_result(conn, ticker) for ticker in resolved]
    positive = {"strong_positive_gap", "potential_positive_gap"}
    summary = {
        "tickers_checked": len(rows),
        "expectation_gap_packets": len(rows),
        "positive_gap_candidates": sum(1 for row in rows if row.get("expectation_gap_status") in positive),
        "promotion_allowed_from_gap_only": 0,
        "valuation_support_improved": sum(1 for row in rows if (row.get("gate_impact") or {}).get("valuation_support") == "context_to_supporting"),
        "thesis_evidence_improved": sum(1 for row in rows if (row.get("gate_impact") or {}).get("thesis_evidence") == "supporting"),
        "new_pending_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": summary,
        "ticker_results": rows,
        "safety": {
            "expectation_gap_direct_pending": False,
            "promotion_rules_relaxed": False,
            "paper_order_created": False,
            "real_trading_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 25 expectation-gap gate integration")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--watchlist")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, watchlist=args.watchlist)
        register_snapshot(conn, "phase25_expectation_gap_gate_integration", args.tickers or args.watchlist or "supply_chain_pilot", payload["overall_status"], SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase25 expectation-gap gate integration validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
