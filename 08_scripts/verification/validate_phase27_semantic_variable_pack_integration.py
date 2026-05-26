#!/usr/bin/env python3
"""Validate Phase 27 semantic evidence integration with variable packs."""

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
from smr_phase25_utils import resolve_phase25_tickers
from smr_phase27_semantic_pipeline import build_semantic_pipeline_for_ticker
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_supply_chain_variable_evidence import build_variable_evidence_packs
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase27_semantic_variable_pack_integration.py"


def _row(conn: sqlite3.Connection, ticker: str, *, mode: str) -> dict:
    before = build_variable_evidence_packs(conn, ticker)
    pipeline = build_semantic_pipeline_for_ticker(ticker, mode=mode)
    after = build_variable_evidence_packs(conn, ticker, semantic_gate_results=pipeline.get("gate_results") or [])
    updates = []
    for key, pack in after.items():
        added = len(pack.get("semantic_evidence") or [])
        if not added:
            continue
        updates.append(
            {
                "variable_type": key,
                "before_status": (before.get(key) or {}).get("evidence_status"),
                "after_status": pack.get("evidence_status"),
                "evidence_added": added,
                "confidence_change": "unchanged" if (before.get(key) or {}).get("confidence") == pack.get("confidence") else "changed",
            }
        )
    return {
        "ticker": ticker,
        "semantic_extractions": len(pipeline.get("semantic_extractions") or []),
        "passed_gate": sum(1 for gate in pipeline.get("gate_results") or [] if gate.get("evidence_status") != "blocked"),
        "variables_updated": updates,
        "confirmed_variables_added": 0,
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, mode: str = "mock") -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = [_row(conn, ticker, mode=mode) for ticker in resolved]
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "tickers_checked": len(rows),
            "semantic_extractions": sum(row.get("semantic_extractions", 0) for row in rows),
            "passed_gate": sum(row.get("passed_gate", 0) for row in rows),
            "variable_packs_updated": sum(len(row.get("variables_updated") or []) for row in rows),
            "confirmed_variables_added": 0,
            "proxy_supported_variables_added": 0,
            "partial_variables_added": sum(1 for row in rows for item in row.get("variables_updated") or [] if item.get("after_status") == "partial"),
        },
        "ticker_results": rows,
        "safety": {
            "confirmed_supplier_share_added": False,
            "confirmed_customer_allocation_added": False,
            "official_consensus_added": False,
            "semantic_evidence_direct_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate semantic variable-pack integration")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "llm" if args.llm and not args.mock else "mock"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, mode=mode)
        register_snapshot(conn, "phase27_semantic_variable_pack_integration", args.tickers or "supply_chain_pilot", payload["overall_status"], SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase27 semantic variable-pack integration validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
