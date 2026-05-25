#!/usr/bin/env python3
"""Phase 15 core blocker recovery diagnostics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from smr_agents import DB_PATH
from smr_fundamentals import latest_fundamentals_snapshot
from smr_cninfo_table_parser import extract_income_statement_fields_from_chunks
from smr_hkex_table_parser import extract_shareholders_equity_from_chunks
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts
from build_phase14_thesis_aware_daily_summary import latest_phase14_validation


SCRIPT_NAME = "validate_phase15_core_blocker_recovery.py"


def _market_for_ticker(ticker: str) -> str:
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return "CN"
    if ticker.endswith(".HK"):
        return "HK"
    return "US"


def _row_for_ticker(validation: dict[str, Any], ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    for row in validation.get("tickers") or []:
        if str(row.get("ticker") or "").upper() == ticker:
            return row
    return {}


def _field_status(snapshot: dict[str, Any], field: str) -> dict[str, Any]:
    details = snapshot.get("field_details") or {}
    detail = details.get(field) or {}
    value = snapshot.get(field)
    if value is None:
        value = detail.get("value") or detail.get("extracted_value")
    evidence_id = detail.get("source_evidence_id")
    evidence_ids = detail.get("source_evidence_ids") or []
    if not evidence_id and evidence_ids:
        evidence_id = evidence_ids[0]
    if value is not None and evidence_id:
        return {
            "status": "extracted",
            "value": value,
            "source_evidence_id": evidence_id,
            "confidence": detail.get("confidence") or snapshot.get("confidence"),
            "allowed_usage": detail.get("allowed_usage") or "supporting_evidence",
        }
    return {
        "status": "missing",
        "missing_reason": detail.get("missing_reason") or (snapshot.get("field_missing_reasons") or {}).get(field) or "field_not_found",
        "confidence": detail.get("confidence") or 0.0,
        "suggested_fix": _suggested_fix(field, _market_for_ticker(str(snapshot.get("ticker") or ""))),
    }


def _suggested_fix(field: str, market: str) -> str:
    if market == "HK" and field == "shareholders_equity":
        return "improve HKEX balance sheet table parser and equity synonym coverage"
    if market == "CN":
        return f"extend CNINFO synonym map and table parser for {field}"
    return f"improve fundamentals extraction for {field}"


def _latest_chunks(conn: sqlite3.Connection, ticker: str, limit: int = 80) -> list[dict[str, Any]]:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='document_chunks'").fetchone()
    if not row:
        return []
    columns = {item[1] for item in conn.execute("PRAGMA table_info(document_chunks)").fetchall()}
    select_columns = [
        column
        for column in ("chunk_id", "document_id", "evidence_id", "chunk_section_type", "text", "published_at", "ingested_at", "created_at")
        if column in columns
    ]
    if not select_columns:
        return []
    order_columns = [column for column in ("created_at", "ingested_at", "published_at") if column in columns]
    if len(order_columns) > 1:
        order_expr = f"datetime(COALESCE({', '.join(order_columns)})) DESC"
    elif len(order_columns) == 1:
        order_expr = f"datetime({order_columns[0]}) DESC"
    else:
        order_expr = "rowid DESC"
    rows = conn.execute(
        f"SELECT {', '.join(select_columns)} FROM document_chunks WHERE ticker=? ORDER BY {order_expr} LIMIT ?",
        (ticker, limit),
    ).fetchall()
    return [dict(zip(select_columns, row)) for row in rows]


def _phase16_recovery_status(conn: sqlite3.Connection, ticker: str, field: str) -> dict[str, Any] | None:
    market = _market_for_ticker(ticker)
    chunks = _latest_chunks(conn, ticker)
    if market == "HK" and field == "shareholders_equity":
        result = extract_shareholders_equity_from_chunks(chunks, ticker=ticker, market="H")
        if result.get("status") == "extracted":
            return result
        return {
            "status": "missing",
            "missing_reason": result.get("missing_reason") or "balance_sheet_not_found",
            "table_detected": result.get("table_detected", False),
            "section_type": result.get("section_type"),
            "confidence": result.get("confidence") or 0.0,
            "allowed_usage": "blocked",
            "suggested_fix": result.get("suggested_fix") or _suggested_fix(field, market),
        }
    if market == "CN" and field in {"revenue", "gross_profit"}:
        result = extract_income_statement_fields_from_chunks(chunks, ticker=ticker)
        status = (result.get("field_status") or {}).get(field) or {}
        if status.get("status") in {"extracted", "derived"}:
            return status
        return {
            "status": "missing",
            "missing_reason": status.get("missing_reason") or result.get("missing_reason") or "income_statement_table_not_found",
            "missing_inputs": status.get("missing_inputs"),
            "table_detected": result.get("table_detected", False),
            "section_type": result.get("section_type"),
            "scope": result.get("scope"),
            "confidence": 0.0,
            "allowed_usage": "blocked",
            "suggested_fix": _suggested_fix(field, market),
        }
    return None


def build_recovery_payload(conn: sqlite3.Connection, ticker: str, *, watchlist_id: str = "ai_core") -> dict[str, Any]:
    ticker = ticker.upper()
    validation = latest_phase14_validation(conn, watchlist_id)
    row = _row_for_ticker(validation, ticker)
    snapshot = latest_fundamentals_snapshot(conn, ticker) or {"ticker": ticker, "field_details": {}, "field_missing_reasons": {}}
    core_before = list(row.get("core_blockers") or [])
    if not core_before:
        core_before = list((row.get("field_gate") or {}).get("core_blockers") or [])
    if not core_before and ticker == "00700.HK":
        core_before = ["shareholders_equity"]
    field_repair = {}
    for field in core_before:
        status = _field_status(snapshot, field)
        if status.get("status") != "extracted":
            phase16_status = _phase16_recovery_status(conn, ticker, field)
            if phase16_status and (
                phase16_status.get("status") in {"extracted", "derived"}
                or status.get("missing_reason") in {"table_not_found", "field_not_found"}
            ):
                status = {**status, **phase16_status}
        field_repair[field] = {"before": "missing" if field in core_before else "unknown", "after": status.get("status"), **status}
    core_after = [field for field, status in field_repair.items() if status.get("status") != "extracted"]
    minimum_fix_path = [
        status.get("suggested_fix")
        for status in field_repair.values()
        if status.get("status") != "extracted" and status.get("suggested_fix")
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "market": _market_for_ticker(ticker),
        "primary_thesis_type": row.get("primary_thesis_type") or "unknown",
        "before_status": row.get("before_status") or row.get("status") or "candidate_shadow",
        "core_blockers_before": core_before,
        "field_repair": field_repair,
        "field_status": field_repair,
        "core_blockers_after": core_after,
        "minimum_fix_path": list(dict.fromkeys(minimum_fix_path)),
        "promotion_result": {
            "status": "candidate_shadow" if core_after else row.get("after_status") or "candidate_shadow",
            "reason": "core_blocker_remaining" if core_after else "core_blocker_repaired_rerun_promotion_required",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 15 core blocker recovery diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="00700.HK")
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_recovery_payload(conn, args.ticker, watchlist_id=args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase15_core_blocker_recovery",
            entity_id=args.ticker.upper(),
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase15 core blocker recovery diagnostics complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
