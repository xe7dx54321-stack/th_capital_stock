#!/usr/bin/env python3
"""Validate Phase 17 financial statement source chunk recovery."""

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
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_TICKERS = ["00700.HK", "300308.SZ", "688041.SH"]


def parse_tickers(raw: str | None, ticker: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if ticker:
        return [ticker.strip().upper()]
    return list(DEFAULT_TICKERS)


def _target_fields(ticker: str) -> list[str]:
    if ticker.endswith(".HK"):
        return ["shareholders_equity"]
    return ["revenue", "gross_profit"]


def _field_before(ticker: str) -> dict[str, dict[str, Any]]:
    if ticker.endswith(".HK"):
        return {"shareholders_equity": {"status": "missing", "missing_reason": "balance_sheet_not_found"}}
    return {
        "revenue": {"status": "missing", "missing_reason": "income_statement_table_not_found"},
        "gross_profit": {"status": "missing", "missing_reason": "income_statement_table_not_found"},
    }


def validate_ticker(db_path: str, ticker: str, *, live: bool = True) -> dict[str, Any]:
    ticker = ticker.upper()
    linkage = link_payload(db_path, ticker, live=live)
    conn = sqlite3.connect(db_path)
    try:
        recovery = build_recovery_payload(conn, ticker)
    finally:
        conn.close()
    field_repair = recovery.get("field_repair") or {}
    after = {field: field_repair.get(field, {"status": "missing", "missing_reason": "field_not_found"}) for field in _target_fields(ticker)}
    chunks = (linkage.get("extraction") or {}).get("chunks") or []
    section_types = {chunk.get("section_type") for chunk in chunks}
    desired_section = "balance_sheet" if ticker.endswith(".HK") else "income_statement"
    repaired = [
        field
        for field, detail in after.items()
        if detail.get("status") in {"extracted", "derived"} and (detail.get("source_evidence_id") or detail.get("input_evidence_ids"))
    ]
    refined = [
        field
        for field, detail in after.items()
        if detail.get("status") not in {"extracted", "derived"}
        and detail.get("missing_reason") not in {"table_not_found", "balance_sheet_not_found", "income_statement_table_not_found"}
    ]
    return {
        "ticker": ticker,
        "before": _field_before(ticker),
        "source_recovery": {
            "financial_statement_source_found": bool(linkage.get("source_found")),
            "balance_sheet_chunk_found": "balance_sheet" in section_types,
            "income_statement_chunk_found": "income_statement" in section_types,
            "evidence_linked": bool(linkage.get("evidence_linked_count")),
            "source_id": linkage.get("source_id"),
            "chunks_found": linkage.get("chunks_found"),
            "evidence_linked_count": linkage.get("evidence_linked_count"),
        },
        "after": after,
        "fields_repaired": repaired,
        "fields_refined": refined,
        "blockers_resolved": [field for field in repaired],
        "blockers_remaining": [field for field, detail in after.items() if detail.get("status") not in {"extracted", "derived"}],
        "desired_section_found": desired_section in section_types,
        "linkage": linkage,
    }


def build_payload(db_path: str, tickers: list[str], *, live: bool = True) -> dict[str, Any]:
    results = [validate_ticker(db_path, ticker, live=live) for ticker in tickers]
    fields_extracted = sum(1 for item in results for detail in (item.get("after") or {}).values() if detail.get("status") == "extracted")
    fields_derived = sum(1 for item in results for detail in (item.get("after") or {}).values() if detail.get("status") == "derived")
    chunks_found = sum((item.get("source_recovery") or {}).get("chunks_found") or 0 for item in results)
    evidence_linked = sum((item.get("source_recovery") or {}).get("evidence_linked_count") or 0 for item in results)
    remaining_table_not_found = sum(
        1
        for item in results
        for detail in (item.get("after") or {}).values()
        if detail.get("missing_reason") in {"table_not_found", "balance_sheet_not_found", "income_statement_table_not_found"}
    )
    payload = {
        "generated_at": now_ts(),
        "overall_status": "pass" if fields_extracted or fields_derived else ("partial_pass" if chunks_found else "diagnostic_only"),
        "targets": results,
        "summary": {
            "targets": tickers,
            "sources_found": sum(1 for item in results if (item.get("source_recovery") or {}).get("financial_statement_source_found")),
            "chunks_found": chunks_found,
            "evidence_linked": evidence_linked,
            "fields_extracted": fields_extracted,
            "fields_derived": fields_derived,
            "remaining_table_not_found": remaining_table_not_found,
            "new_pending_created": 0,
        },
    }
    conn = sqlite3.connect(db_path)
    try:
        register_snapshot(
            conn,
            entity_type="phase17_source_chunk_recovery",
            entity_id="latest",
            status=payload["overall_status"],
            source="validate_phase17_source_chunk_recovery.py",
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 17 source chunk recovery")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.db_path, parse_tickers(args.tickers, args.ticker), live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("validate_phase17_source_chunk_recovery.py", "success", "phase17 source chunk recovery validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
