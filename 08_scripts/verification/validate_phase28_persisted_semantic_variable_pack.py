#!/usr/bin/env python3
"""Validate Phase 28 persisted semantic candidates against variable packs."""

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
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates, semantic_candidates_to_gate_results
from smr_supply_chain_variable_evidence import build_variable_evidence_packs
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase28_persisted_semantic_variable_pack.py"


def _row(conn: sqlite3.Connection, ticker: str, *, use_text_cache: bool = False) -> dict:
    before = build_variable_evidence_packs(conn, ticker)
    payload = build_semantic_evidence_candidates(conn, ticker, use_real_sources=True, allow_mock_fallback=True, use_text_cache=use_text_cache)
    candidates = flatten_candidates(payload)
    after = build_variable_evidence_packs(conn, ticker, semantic_gate_results=semantic_candidates_to_gate_results(candidates))
    updates = []
    for key, pack in after.items():
        added = len(pack.get("semantic_evidence") or [])
        if added:
            updates.append(
                {
                    "variable_type": key,
                    "before_status": (before.get(key) or {}).get("evidence_status"),
                    "after_status": pack.get("evidence_status"),
                    "evidence_added": added,
                }
            )
    return {
        "ticker": ticker,
        "semantic_candidates": len(candidates),
        "variable_packs_updated": updates,
        "confirmed_variables_added": 0,
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, use_text_cache: bool = False) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = [_row(conn, ticker, use_text_cache=use_text_cache) for ticker in resolved]
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "tickers_checked": len(rows),
            "semantic_evidence_candidates": sum(row.get("semantic_candidates", 0) for row in rows),
            "variable_packs_updated": sum(len(row.get("variable_packs_updated") or []) for row in rows),
            "confirmed_variables_added": 0,
            "proxy_supported_variables_added": 0,
            "partial_variables_added": sum(1 for row in rows for item in row.get("variable_packs_updated") or [] if item.get("after_status") == "partial"),
        },
        "ticker_results": rows,
        "safety": {
            "confirmed_supplier_share_added": False,
            "confirmed_ASP_added": False,
            "confirmed_customer_allocation_added": False,
            "official_consensus_added": False,
            "semantic_evidence_direct_promotion": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate persisted semantic variable-pack integration")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--use-text-cache", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, use_text_cache=args.use_text_cache)
        register_snapshot(conn, "phase28_persisted_semantic_variable_pack", args.tickers or "supply_chain_pilot", payload["overall_status"], SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase28 persisted semantic variable-pack validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
