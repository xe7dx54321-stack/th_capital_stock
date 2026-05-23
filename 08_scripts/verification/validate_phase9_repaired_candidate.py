#!/usr/bin/env python3
"""Phase 9 repaired candidate before/after validator."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, JOBS_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase9_data_quality_diagnostics import build_diagnostics
from repair_valuation_snapshot import repair_valuation_for_ticker
from run_phase9_repair_queue import execute_task, select_tasks
from smr_agents import DB_PATH
from smr_bear_case_response import respond_to_bear_case
from smr_blocker_taxonomy import normalize_blockers
from smr_fundamentals import latest_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import diagnose_valuation_snapshot, latest_valuation_snapshot
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase9_repaired_candidate.py"


def run_command(command: list[str], timeout: int = 240) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout": exc.stdout if isinstance(exc.stdout, str) else "",
            "stderr": f"timeout_after_{timeout}s",
        }


def parse_json_stdout(run: dict[str, Any]) -> dict[str, Any]:
    stdout = run.get("stdout") or ""
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start < 0 or end <= start:
        return {"parse_error": "json_payload_not_found", "stdout_tail": stdout[-1000:], "stderr_tail": (run.get("stderr") or "")[-1000:]}
    try:
        return json.loads(stdout[start : end + 1])
    except json.JSONDecodeError as exc:
        return {"parse_error": str(exc), "stdout_tail": stdout[-1000:], "stderr_tail": (run.get("stderr") or "")[-1000:]}


def run_phase6_single(ticker: str, days: int, timeout: int) -> dict[str, Any]:
    script = Path(__file__).with_name("validate_phase6_multi_ticker_live.py")
    command = [
        sys.executable,
        str(script),
        "--tickers",
        ticker,
        "--days",
        str(days),
        "--timeout",
        str(timeout),
    ]
    return parse_json_stdout(run_command(command, timeout=timeout + 30))


def ticker_result(payload: dict[str, Any], ticker: str) -> dict[str, Any]:
    for item in payload.get("tickers") or []:
        if str(item.get("ticker") or "").upper() == ticker.upper():
            return item
    return {}


def blocker_codes(item: dict[str, Any]) -> list[str]:
    return [blocker.get("code") for blocker in normalize_blockers(item.get("blocking_factors") or []) if blocker.get("code")]


def field_state(snapshot: dict[str, Any]) -> tuple[list[str], list[str]]:
    details = snapshot.get("field_details") or {}
    missing = []
    repaired = []
    for field in ("gross_profit", "eps_basic", "capex", "free_cash_flow", "shareholders_equity"):
        detail = details.get(field) or {}
        value = detail.get("extracted_value")
        if value is None and snapshot.get(field) is not None:
            value = snapshot.get(field)
        if value is None or detail.get("missing_reason"):
            missing.append(field)
        else:
            repaired.append(field)
    return repaired, missing


def build_bear_response_from_result(item: dict[str, Any], snapshot: dict[str, Any], valuation: dict[str, Any]) -> dict[str, Any]:
    response = item.get("bear_case_response")
    if response:
        return response
    evidence_rows = [
        {"evidence_id": evidence_id, "source_type": "filing", "usable_for_promotion": True, "quality_score": 0.7, "metadata": {"live": True}}
        for evidence_id in item.get("live_evidence_ids") or []
    ]
    return respond_to_bear_case(
        item.get("ticker") or "",
        {
            "bear_case_strength": item.get("bear_case_strength"),
            "bear_case_claims": [{"claim_text": "high bear case remains", "severity": item.get("bear_case_strength") or "medium"}],
        },
        evidence_rows=evidence_rows,
        fundamentals_snapshot=snapshot,
        valuation_snapshot=valuation,
    )


def validate_repaired_candidate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    days: int = 365,
    timeout: int = 240,
    run_repairs: bool = False,
) -> dict[str, Any]:
    before_payload = run_phase6_single(ticker, days, timeout)
    before_item = ticker_result(before_payload, ticker)
    before_snapshot = latest_fundamentals_snapshot(conn, ticker)
    before_valuation = latest_valuation_snapshot(conn, ticker)
    before_codes = blocker_codes(before_item)

    valuation_repair = repair_valuation_for_ticker(conn, ticker, dry_run=not run_repairs)
    data_quality = build_diagnostics(conn, ticker, refresh_fundamentals=run_repairs)
    repair_queue_results: list[dict[str, Any]] = []
    if run_repairs:
        for task in select_tasks(conn, ticker=ticker, limit=6):
            repair_queue_results.append(execute_task(conn, task, dry_run=False))

    after_payload = run_phase6_single(ticker, days, timeout) if run_repairs else before_payload
    after_item = ticker_result(after_payload, ticker)
    after_snapshot = latest_fundamentals_snapshot(conn, ticker)
    after_valuation = latest_valuation_snapshot(conn, ticker)
    after_codes = blocker_codes(after_item)
    fields_repaired, fields_missing = field_state(after_snapshot)
    bear_response = build_bear_response_from_result(after_item, after_snapshot, after_valuation)
    valuation_diagnostics = diagnose_valuation_snapshot(conn, ticker, before=after_valuation)

    payload = {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "before_status": before_item.get("status") or "unknown",
        "after_status": after_item.get("status") or "unknown",
        "promotion_allowed": bool(after_item.get("promotion_allowed")),
        "live_evidence_used": bool(
            after_item.get("status") == "pending_human_review"
            and (int(after_item.get("live_filing_evidence") or 0) > 0 or int(after_item.get("live_news_evidence") or 0) > 0)
        ),
        "blockers_resolved": sorted(set(before_codes) - set(after_codes)),
        "blockers_remaining": after_codes,
        "valuation_sub_blockers_remaining": valuation_diagnostics.get("sub_blockers") or [],
        "fields_repaired": fields_repaired,
        "fields_still_missing": fields_missing,
        "data_quality_root_causes": data_quality.get("root_causes") or [],
        "bear_case_response_status": bear_response.get("overall_response_status"),
        "bear_case_response": bear_response,
        "candidate_action": after_item.get("action"),
        "decision_ledger_written": bool(after_item.get("ledger_written")),
        "run_repairs": run_repairs,
        "valuation_repair": valuation_repair,
        "repair_queue_results": repair_queue_results,
        "before_run_id": before_payload.get("run_id"),
        "after_run_id": after_payload.get("run_id"),
        "phase6_before_summary": before_payload.get("summary") or {},
        "phase6_after_summary": after_payload.get("summary") or {},
    }
    register_snapshot(
        conn,
        entity_type="phase9_repaired_candidate_validation",
        entity_id=ticker.upper(),
        status=payload["after_status"],
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9 repaired candidate")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="09988.HK")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--run-repairs", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = validate_repaired_candidate(
            conn,
            args.ticker,
            days=args.days,
            timeout=args.timeout,
            run_repairs=args.run_repairs,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase9 repaired candidate validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
