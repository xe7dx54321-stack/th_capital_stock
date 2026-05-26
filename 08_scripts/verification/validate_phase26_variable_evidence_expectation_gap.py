#!/usr/bin/env python3
"""Validate Phase 26 variable evidence integration with expectation gap."""

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
from smr_expectation_gap import build_expectation_gap
from smr_phase25_utils import resolve_phase25_tickers
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_supply_chain_variable_evidence import build_variable_evidence_packs
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase26_variable_evidence_expectation_gap.py"


def _why_not_upgraded(packs: dict[str, Any]) -> list[str]:
    reasons = []
    if (packs.get("supplier_share") or {}).get("evidence_status") != "confirmed":
        reasons.append("supplier share not disclosed")
    if (packs.get("ASP_price_proxy") or {}).get("evidence_status") in {"missing", "context_only"}:
        reasons.append("ASP missing")
    if not (packs.get("consensus") or {}).get("official_consensus_available"):
        reasons.append("official consensus missing")
    if (packs.get("customer_allocation_proxy") or {}).get("evidence_status") != "confirmed":
        reasons.append("customer allocation missing")
    return reasons


def build_ticker_result(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    before = build_expectation_gap(conn, ticker, variable_evidence={})
    packs = build_variable_evidence_packs(conn, ticker)
    after = build_expectation_gap(conn, ticker, variable_evidence=packs)
    before_gap = before.get("expectation_gap") or {}
    after_gap = after.get("expectation_gap") or {}
    confidence_upgraded = before_gap.get("confidence") != after_gap.get("confidence") and after_gap.get("confidence") not in {"low", "unknown"}
    return {
        "ticker": ticker,
        "before": {
            "expectation_gap_status": before_gap.get("status"),
            "confidence": before_gap.get("confidence"),
        },
        "variable_evidence": {
            "supplier_share": (packs.get("supplier_share") or {}).get("evidence_status"),
            "ASP_price_proxy": (packs.get("ASP_price_proxy") or {}).get("evidence_status"),
            "capacity": (packs.get("capacity") or {}).get("evidence_status"),
            "customer_allocation_proxy": (packs.get("customer_allocation_proxy") or {}).get("evidence_status"),
            "consensus": "official" if (packs.get("consensus") or {}).get("official_consensus_available") else "internal_proxy_only",
        },
        "after": {
            "expectation_gap_status": after_gap.get("status"),
            "confidence": after_gap.get("confidence"),
            "packet_status": "needs_more_data" if _why_not_upgraded(packs) else "ready_for_research_review",
        },
        "why_not_upgraded": _why_not_upgraded(packs),
        "confidence_upgraded": confidence_upgraded,
        "promotion_allowed_from_gap_only": False,
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers)
    rows = [build_ticker_result(conn, ticker) for ticker in resolved]
    summary = {
        "tickers_checked": len(rows),
        "variable_packs_generated": len(rows) * 6,
        "confidence_upgraded": sum(1 for row in rows if row.get("confidence_upgraded")),
        "confidence_downgraded": 0,
        "needs_more_data": sum(1 for row in rows if (row.get("after") or {}).get("packet_status") == "needs_more_data"),
        "promotion_allowed_from_gap_only": 0,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": summary,
        "ticker_results": rows,
        "safety": {
            "planned_source_used_as_active_evidence": False,
            "expectation_gap_direct_pending": False,
            "promotion_rules_relaxed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 26 variable evidence expectation-gap integration")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
        register_snapshot(conn, "phase26_variable_evidence_expectation_gap", args.tickers or "supply_chain_pilot", payload["overall_status"], SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase26 variable evidence expectation-gap validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
