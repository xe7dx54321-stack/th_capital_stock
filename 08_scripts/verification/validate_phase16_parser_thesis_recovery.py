#!/usr/bin/env python3
"""Phase 16 parser and thesis metadata recovery validator."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, REPORTING_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from apply_watchlist_metadata_patch import build_patch_result
from build_phase15_unknown_thesis_diagnostics import build_ticker_payload
from validate_phase15_core_blocker_recovery import build_recovery_payload
from smr_agents import DB_PATH
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase16_parser_thesis_recovery.py"
DEFAULT_TICKERS = ["00700.HK", "300308.SZ", "688041.SH", "002230.SZ"]


def _target_type(ticker: str) -> str:
    if ticker.endswith(".HK"):
        return "hkex_balance_sheet_recovery"
    if ticker.endswith((".SZ", ".SH", ".BJ")) and ticker != "002230.SZ":
        return "cninfo_income_statement_recovery"
    return "unknown_thesis_recovery"


def _fields_repaired(field_repair: dict[str, Any]) -> list[str]:
    return [
        field
        for field, status in field_repair.items()
        if status.get("status") in {"extracted", "derived"} and (status.get("source_evidence_id") or status.get("input_evidence_ids"))
    ]


def _fields_refined(field_repair: dict[str, Any]) -> list[str]:
    legacy = {"table_not_found", "field_not_found"}
    refined = []
    for field, status in field_repair.items():
        if status.get("status") in {"extracted", "derived"}:
            continue
        reason = status.get("missing_reason")
        if reason and reason not in legacy:
            refined.append(field)
    return refined


def build_target(conn: sqlite3.Connection, ticker: str, *, execute_metadata_patch: bool = False) -> dict[str, Any]:
    ticker = ticker.upper()
    if ticker == "002230.SZ":
        diagnostics = build_ticker_payload(conn, ticker)
        simulation = diagnostics.get("after_patch_simulation") or {}
        patch_result = build_patch_result(ticker, execute=execute_metadata_patch)
        return {
            "ticker": ticker,
            "target_type": "unknown_thesis_recovery",
            "before_thesis": diagnostics.get("current_thesis_type"),
            "after_thesis": simulation.get("candidate_thesis_type"),
            "confidence_before": diagnostics.get("inference_confidence"),
            "confidence_after": simulation.get("simulated_confidence"),
            "unknown_reasons": diagnostics.get("unknown_reasons") or [],
            "suggested_metadata_patch": diagnostics.get("suggested_metadata_patch") or {},
            "metadata_patch": patch_result,
            "allow_pending": False,
            "reason": simulation.get("reason"),
        }
    recovery = build_recovery_payload(conn, ticker)
    field_repair = recovery.get("field_repair") or {}
    repaired = _fields_repaired(field_repair)
    refined = _fields_refined(field_repair)
    return {
        "ticker": ticker,
        "target_type": _target_type(ticker),
        "before_core_blockers": recovery.get("core_blockers_before") or [],
        "after_core_blockers": recovery.get("core_blockers_after") or [],
        "fields_repaired": repaired,
        "fields_refined": refined,
        "remaining_blockers": recovery.get("core_blockers_after") or [],
        "field_repair": field_repair,
        "promotion_result": recovery.get("promotion_result") or {},
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, execute_metadata_patch: bool = False) -> dict[str, Any]:
    targets = [build_target(conn, ticker, execute_metadata_patch=execute_metadata_patch) for ticker in tickers]
    core_resolved = sum(len(target.get("fields_repaired") or []) for target in targets)
    core_refined = sum(len(target.get("fields_refined") or []) for target in targets)
    core_remaining = sum(len(target.get("remaining_blockers") or []) for target in targets)
    unknown_improved = sum(
        1
        for target in targets
        if target.get("target_type") == "unknown_thesis_recovery"
        and target.get("before_thesis") == "unknown"
        and target.get("after_thesis") not in {None, "unknown"}
    )
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if (core_resolved or core_refined or unknown_improved) else "diagnostic_only",
        "targets": targets,
        "summary": {
            "core_blockers_resolved": core_resolved,
            "core_blockers_refined": core_refined,
            "core_blockers_remaining": core_remaining,
            "unknown_thesis_improved": unknown_improved,
            "new_pending_created": 0,
        },
    }


def parse_tickers(raw: str | None) -> list[str]:
    if not raw:
        return DEFAULT_TICKERS
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 16 parser and thesis recovery")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--execute-metadata-patch", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, parse_tickers(args.tickers), execute_metadata_patch=args.execute_metadata_patch)
        register_snapshot(
            conn,
            entity_type="phase16_parser_thesis_recovery",
            entity_id="latest",
            status=payload.get("overall_status"),
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase16 parser thesis recovery validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
