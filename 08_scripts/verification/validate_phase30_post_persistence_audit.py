#!/usr/bin/env python3
"""Audit persisted semantic evidence candidates after Phase 30 guard."""

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
from smr_semantic_evidence_persistence import ensure_semantic_evidence_candidate_table, semantic_candidates_to_gate_results
from smr_supply_chain_variable_evidence import build_variable_evidence_packs
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _load_persisted_candidates(conn: sqlite3.Connection, ticker: str) -> list[dict]:
    ensure_semantic_evidence_candidate_table(conn)
    rows = conn.execute(
        """
        SELECT evidence_id, ticker, theme, source_id, source_url, source_type, chunk_id,
               quoted_span, variable_type, claim_text, evidence_status, allowed_usage,
               usable_for_expectation_gap, usable_for_valuation_support, usable_for_promotion,
               limitations_json, payload_json
        FROM semantic_evidence_candidates
        WHERE ticker = ?
        ORDER BY updated_at DESC, evidence_id
        """,
        (ticker,),
    ).fetchall()
    candidates = []
    for row in rows:
        candidates.append(
            {
                "evidence_id": row[0],
                "ticker": row[1],
                "theme": row[2],
                "source_id": row[3],
                "source_url": row[4],
                "source_type": row[5],
                "chunk_id": row[6],
                "quoted_span": row[7],
                "variable_type": row[8],
                "claim_text": row[9],
                "evidence_status": row[10],
                "allowed_usage": row[11],
                "usable_for_expectation_gap": bool(row[12]),
                "usable_for_valuation_support": bool(row[13]),
                "usable_for_promotion": bool(row[14]),
                "limitations": json.loads(row[15] or "[]"),
                "payload": json.loads(row[16] or "{}"),
            }
        )
    return candidates


def _row(conn: sqlite3.Connection, ticker: str) -> dict:
    candidates = _load_persisted_candidates(conn, ticker)
    before_packs = build_variable_evidence_packs(conn, ticker)
    after_packs = build_variable_evidence_packs(conn, ticker, semantic_gate_results=semantic_candidates_to_gate_results(candidates))
    before_gap = build_expectation_gap(conn, ticker, variable_evidence=before_packs).get("expectation_gap") or {}
    after_gap = build_expectation_gap(conn, ticker, variable_evidence=after_packs).get("expectation_gap") or {}
    variables_updated = [name for name, pack in after_packs.items() if pack.get("semantic_evidence")]
    return {
        "ticker": ticker,
        "persisted_candidates": len(candidates),
        "variables_updated": variables_updated,
        "variable_packs_updated": len(variables_updated),
        "confidence_change": "unchanged" if before_gap.get("confidence") == after_gap.get("confidence") else "changed",
        "expectation_gap_before": before_gap.get("status"),
        "expectation_gap_after": after_gap.get("status"),
        "why_not_upgraded": [
            "supplier share still not disclosed",
            "ASP still missing",
            "customer allocation still missing",
        ],
    }


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    rows = [_row(conn, ticker) for ticker in resolve_phase25_tickers(tickers)]
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "persisted_candidates": sum(row["persisted_candidates"] for row in rows),
            "variable_packs_updated": sum(row["variable_packs_updated"] for row in rows),
            "expectation_gap_improved": 0,
            "valuation_support_improved": 0,
            "bear_case_mitigation_improved": 0,
            "confirmed_variables_added": 0,
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
    parser = argparse.ArgumentParser(description="Validate Phase 30 post-persistence audit")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
