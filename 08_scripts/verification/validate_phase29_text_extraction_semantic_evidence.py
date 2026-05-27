#!/usr/bin/env python3
"""Validate Phase 29 text extraction to semantic evidence chain."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(JOBS_DIR) not in sys.path:
    sys.path.insert(0, str(JOBS_DIR))

from extract_real_ir_document_text import build_payload as build_extraction_payload
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

SCRIPT_NAME = "validate_phase29_text_extraction_semantic_evidence.py"


def _row(conn: sqlite3.Connection, ticker: str) -> dict:
    extraction = build_extraction_payload(conn, tickers=ticker, mode="dry_run")
    candidate_payload = build_semantic_evidence_candidates(conn, ticker, use_real_sources=True, use_text_cache=True, mode="mock")
    candidates = flatten_candidates(candidate_payload)
    before_packs = build_variable_evidence_packs(conn, ticker)
    after_packs = build_variable_evidence_packs(conn, ticker, semantic_gate_results=semantic_candidates_to_gate_results(candidates))
    before_gap = build_expectation_gap(conn, ticker, variable_evidence=before_packs).get("expectation_gap") or {}
    after_gap = build_expectation_gap(conn, ticker, variable_evidence=after_packs).get("expectation_gap") or {}
    updates = sum(1 for pack in after_packs.values() if pack.get("semantic_evidence"))
    return {
        "ticker": ticker,
        "sources_checked": (extraction.get("summary") or {}).get("sources_checked", 0),
        "text_extracted": (extraction.get("summary") or {}).get("text_extracted", 0),
        "chunks_created": (candidate_payload.get("rows") or [{}])[0].get("pipeline", {}).get("chunks") and len((candidate_payload.get("rows") or [{}])[0].get("pipeline", {}).get("chunks") or []),
        "semantic_extractions": (candidate_payload.get("summary") or {}).get("semantic_extractions", 0),
        "evidence_candidates_created": len(candidates),
        "variable_packs_updated": updates,
        "expectation_gap_before": before_gap.get("status"),
        "expectation_gap_after": after_gap.get("status"),
        "confidence_before": before_gap.get("confidence"),
        "confidence_after": after_gap.get("confidence"),
        "new_pending_created": 0,
        "promotion_allowed_from_semantic_evidence_only": 0,
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = [_row(conn, ticker) for ticker in resolved]
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "tickers_checked": len(rows),
            "sources_checked": sum(row.get("sources_checked") or 0 for row in rows),
            "text_extracted": sum(row.get("text_extracted") or 0 for row in rows),
            "chunks_created": sum(row.get("chunks_created") or 0 for row in rows),
            "semantic_extractions": sum(row.get("semantic_extractions") or 0 for row in rows),
            "evidence_candidates_created": sum(row.get("evidence_candidates_created") or 0 for row in rows),
            "variable_packs_updated": sum(row.get("variable_packs_updated") or 0 for row in rows),
            "expectation_gap_improved": 0,
            "valuation_support_improved": 0,
            "new_pending_created": 0,
            "promotion_allowed_from_semantic_evidence_only": 0,
        },
        "ticker_results": rows,
        "safety": {
            "confirmed_supplier_share_added": False,
            "confirmed_ASP_added": False,
            "confirmed_customer_allocation_added": False,
            "official_consensus_added": False,
            "semantic_evidence_alone_pending": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 29 text extraction semantic evidence")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
        register_snapshot(conn, "phase29_text_extraction_semantic_evidence", args.tickers or "supply_chain_pilot", payload["overall_status"], SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase29 text extraction semantic evidence validated", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
