#!/usr/bin/env python3
"""Phase 10 repaired-candidate validation for valuation input hardening."""

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
from run_phase10_repair_resolution import resolve_tasks
from smr_agents import DB_PATH
from smr_bear_case_response import respond_to_bear_case
from smr_blocker_taxonomy import normalize_blockers
from smr_fundamentals import latest_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import diagnose_valuation_snapshot, latest_valuation_snapshot
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase10_repaired_candidate.py"


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
        return {"returncode": result.returncode, "stdout": result.stdout or "", "stderr": result.stderr or "", "command": command}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout if isinstance(exc.stdout, str) else "", "stderr": f"timeout_after_{timeout}s", "command": command}


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
    return parse_json_stdout(
        run_command(
            [sys.executable, str(script), "--tickers", ticker, "--days", str(days), "--timeout", str(timeout)],
            timeout=timeout + 30,
        )
    )


def ticker_result(payload: dict[str, Any], ticker: str) -> dict[str, Any]:
    for item in payload.get("tickers") or []:
        if str(item.get("ticker") or "").upper() == ticker.upper():
            return item
    return {}


def blocker_codes(item: dict[str, Any]) -> list[str]:
    return [blocker.get("code") for blocker in normalize_blockers(item.get("blocking_factors") or []) if blocker.get("code")]


def valuation_summary(snapshot: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_usage": snapshot.get("allowed_usage"),
        "valuation_status": snapshot.get("valuation_status"),
        "price_status": diagnostics.get("price_status") or snapshot.get("price_status"),
        "price_trade_date": snapshot.get("price_trade_date") or (snapshot.get("metadata") or {}).get("price_trade_date"),
        "peer_set_id": snapshot.get("peer_set_id"),
        "peer_set_status": snapshot.get("peer_set_status"),
        "peer_count_available": snapshot.get("peer_count_available"),
        "peer_count_required": snapshot.get("peer_count_required"),
        "historical_percentile_status": snapshot.get("historical_percentile_status"),
        "forward_eps_status": (snapshot.get("forward_eps") or {}).get("status") or ("proxy" if snapshot.get("broker_forward_eps_proxy") else "missing"),
        "forward_eps": snapshot.get("forward_eps") or {},
        "sub_blockers": diagnostics.get("sub_blockers") or [],
    }


def build_bear_response(item: dict[str, Any], fundamentals: dict[str, Any], valuation: dict[str, Any]) -> dict[str, Any]:
    if item.get("bear_case_response"):
        return item["bear_case_response"]
    evidence_rows = [
        {"evidence_id": evidence_id, "source_type": "filing", "usable_for_promotion": True, "quality_score": 0.7, "metadata": {"live": True}}
        for evidence_id in item.get("live_evidence_ids") or []
    ]
    claims = [
        {"claim_text": "growth uncertainty remains high", "severity": item.get("bear_case_strength") or "medium"},
        {"claim_text": "valuation rerating lacks support", "severity": item.get("bear_case_strength") or "medium"},
    ]
    return respond_to_bear_case(
        item.get("ticker") or "",
        {"bear_case_strength": item.get("bear_case_strength"), "bear_case_claims": claims},
        evidence_rows=evidence_rows,
        fundamentals_snapshot=fundamentals,
        valuation_snapshot=valuation,
    )


def validate_phase10_candidate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    days: int = 365,
    timeout: int = 240,
    run_repairs: bool = False,
) -> dict[str, Any]:
    before_payload = run_phase6_single(ticker, days, timeout)
    before_item = ticker_result(before_payload, ticker)
    before_codes = blocker_codes(before_item)
    before_valuation = latest_valuation_snapshot(conn, ticker)
    before_diagnostics = diagnose_valuation_snapshot(conn, ticker, before=before_valuation)

    valuation_repair = repair_valuation_for_ticker(conn, ticker, dry_run=not run_repairs)
    after_payload = run_phase6_single(ticker, days, timeout) if run_repairs else before_payload
    after_item = ticker_result(after_payload, ticker)
    after_codes = blocker_codes(after_item)
    after_valuation = latest_valuation_snapshot(conn, ticker)
    after_diagnostics = diagnose_valuation_snapshot(conn, ticker, before=after_valuation)
    fundamentals = latest_fundamentals_snapshot(conn, ticker)
    data_quality = build_diagnostics(conn, ticker, refresh_fundamentals=False)
    bear_response = build_bear_response(after_item, fundamentals, after_valuation)
    valuation_after_summary = valuation_summary(after_valuation, after_diagnostics)
    validation_blockers = sorted(set(after_codes + (after_diagnostics.get("sub_blockers") or [])))
    resolution = resolve_tasks(conn, ticker=ticker, validation_blockers=validation_blockers, dry_run=True, limit=20)

    payload = {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "before_status": before_item.get("status") or "unknown",
        "after_status": after_item.get("status") or "unknown",
        "promotion_allowed": bool(after_item.get("promotion_allowed")),
        "blockers_resolved": sorted(set(before_codes + (before_diagnostics.get("sub_blockers") or [])) - set(validation_blockers)),
        "blockers_remaining": validation_blockers,
        "valuation": valuation_after_summary,
        "valuation_repair": valuation_repair,
        "data_quality_status": data_quality.get("overall_data_quality_status"),
        "bear_case_response": bear_response.get("bear_case_response_summary") or {
            "overall_status": bear_response.get("overall_response_status"),
            "action_effect": bear_response.get("action_effect"),
        },
        "bear_case_response_detail": bear_response,
        "candidate": {
            "action": after_item.get("action"),
            "position_size": (after_item.get("portfolio_risk") or {}).get("recommended_position_pct") or 0,
            "status": after_item.get("status"),
        },
        "decision_ledger_written": bool(after_item.get("ledger_written")),
        "repair_resolution": resolution,
        "run_repairs": run_repairs,
        "before_run_id": before_payload.get("run_id"),
        "after_run_id": after_payload.get("run_id"),
    }
    register_snapshot(
        conn,
        entity_type="phase10_repaired_candidate_validation",
        entity_id=ticker.upper(),
        status=payload["after_status"],
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 10 repaired candidate")
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
        payload = validate_phase10_candidate(
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
    log_run(SCRIPT_NAME, "success", "phase10 repaired candidate validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
