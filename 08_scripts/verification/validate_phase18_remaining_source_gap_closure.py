#!/usr/bin/env python3
"""Validate remaining 688041.SH source gap closure and field recovery."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from link_financial_statement_chunks_to_evidence import build_payload as link_payload
from validate_phase15_core_blocker_recovery import build_recovery_payload
from smr_agents import DB_PATH
from smr_recovered_fundamentals import recovered_fields_from_chunks
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _target_fields(ticker: str) -> list[str]:
    return ["shareholders_equity"] if ticker.upper().endswith(".HK") else ["revenue", "gross_profit"]


def _before_for_ticker(ticker: str) -> dict[str, dict[str, Any]]:
    reason = "balance_sheet_not_found" if ticker.upper().endswith(".HK") else "financial_statement_source_not_found"
    return {field: {"status": "missing", "missing_reason": reason} for field in _target_fields(ticker)}


def _normalize_recovered_detail(detail: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(detail)
    if normalized.get("value") is None and normalized.get("extracted_value") is not None:
        normalized["value"] = normalized.get("extracted_value")
    normalized.setdefault("allowed_usage", "supporting_evidence")
    return normalized


def validate_ticker(db_path: str, ticker: str, *, live: bool = True) -> dict[str, Any]:
    ticker = ticker.upper()
    linkage = link_payload(db_path, ticker, live=live)
    conn = sqlite3.connect(db_path)
    try:
        recovery = build_recovery_payload(conn, ticker)
        chunk_recovered = recovered_fields_from_chunks(conn, ticker)
        register_payload = None
    finally:
        conn.close()
    field_repair = recovery.get("field_repair") or {}
    after = {}
    for field in _target_fields(ticker):
        if field in field_repair:
            after[field] = field_repair[field]
        elif field in chunk_recovered:
            after[field] = _normalize_recovered_detail(chunk_recovered[field])
        else:
            after[field] = {"status": "missing", "missing_reason": "field_not_found"}
    chunks = (linkage.get("extraction") or {}).get("chunks") or []
    section_types = {chunk.get("section_type") for chunk in chunks}
    source_found = bool(linkage.get("source_found"))
    income_found = "income_statement" in section_types
    evidence_linked = bool(linkage.get("evidence_linked_count"))
    repaired = [
        field
        for field, detail in after.items()
        if detail.get("status") in {"extracted", "derived"} and (detail.get("source_evidence_id") or detail.get("input_evidence_ids"))
    ]
    remaining = [field for field, detail in after.items() if detail.get("status") not in {"extracted", "derived"}]
    resolved = []
    if source_found:
        resolved.append("financial_statement_source_not_found")
    if income_found:
        resolved.append("income_statement_table_not_found")
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker,
        "before": _before_for_ticker(ticker),
        "source_recovery": {
            "financial_statement_source_found": source_found,
            "income_statement_chunk_found": income_found,
            "balance_sheet_chunk_found": "balance_sheet" in section_types,
            "evidence_linked": evidence_linked,
            "source_id": linkage.get("source_id"),
            "chunks_found": linkage.get("chunks_found"),
            "evidence_linked_count": linkage.get("evidence_linked_count"),
            "missing_reason": linkage.get("missing_reason"),
        },
        "after": after,
        "fields_repaired": repaired,
        "blockers_resolved": list(dict.fromkeys(resolved)),
        "blockers_remaining": remaining,
    }
    conn = sqlite3.connect(db_path)
    try:
        register_snapshot(
            conn,
            entity_type="phase18_remaining_source_gap_closure",
            entity_id=ticker,
            status="pass" if repaired else ("partial_pass" if source_found or income_found else "missing"),
            source="validate_phase18_remaining_source_gap_closure.py",
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 18 remaining source gap closure")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = validate_ticker(args.db_path, args.ticker, live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("validate_phase18_remaining_source_gap_closure.py", "success", "phase18 source gap closure validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
