#!/usr/bin/env python3
"""Phase 11 validation for peer and historical valuation completion."""

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

from build_historical_valuation_snapshot import build_historical_valuation_payload
from build_peer_valuation_data import build_peer_valuation_payload
from build_phase9_data_quality_diagnostics import (
    build_diagnostics,
    data_quality_status,
    field_changes,
    field_quality_from_snapshot,
    root_cause_keys,
    root_causes_from_field_quality,
)
from repair_valuation_snapshot import repair_valuation_for_ticker
from run_phase10_repair_resolution import resolve_tasks
from smr_agents import DB_PATH
from smr_bear_case_response import respond_to_bear_case
from smr_blocker_taxonomy import normalize_blockers
from smr_fundamentals import FUNDAMENTAL_FIELDS, build_fundamentals_snapshot, latest_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import diagnose_valuation_snapshot, latest_valuation_snapshot, valuation_sub_blockers
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase11_peer_historical_repaired_candidate.py"


def loads(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


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
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        return {"returncode": 124, "stdout": stdout, "stderr": f"timeout_after_{timeout}s", "command": command}


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


def _decode_valuation_row(row: sqlite3.Row) -> dict[str, Any]:
    metadata = loads(row["metadata_json"], {})
    inputs = metadata.get("inputs_used") or {}
    peer_comparison = inputs.get("peer_set") or loads(row["peer_comparison_json"], {})
    historical = inputs.get("historical_valuation") or {}
    data = {
        "id": row["id"],
        "ticker": row["ticker"],
        "market": row["market"],
        "generated_at": row["generated_at"],
        "valuation_available": bool(row["valuation_available"]),
        "current_price": row["current_price"],
        "market_cap": row["market_cap"],
        "pe_ttm": row["pe_ttm"],
        "ps_ttm": row["ps_ttm"],
        "pb": row["pb"],
        "historical_percentile": row["historical_percentile"],
        "peer_comparison": peer_comparison,
        "valuation_status": row["valuation_status"],
        "missing_data": loads(row["missing_data_json"], []),
        "allowed_usage": row["allowed_usage"],
        "metadata": metadata,
        "ev_ebitda_ttm": row["ev_ebitda_ttm"],
        "broker_forward_eps_proxy": row["broker_forward_eps_proxy"],
        "valuation_confidence": row["valuation_confidence"],
        "peer_set": loads(row["peer_set_json"], []),
        "price_trade_date": metadata.get("price_trade_date"),
        "price_status": metadata.get("price_status"),
        "peer_set_id": metadata.get("peer_set_id") or peer_comparison.get("peer_set_id"),
        "peer_set_status": metadata.get("peer_set_status") or peer_comparison.get("peer_set_status"),
        "peer_count_available": metadata.get("peer_count_available") or peer_comparison.get("peer_count_available"),
        "peer_count_required": metadata.get("peer_count_required") or peer_comparison.get("peer_count_required"),
        "historical_valuation": historical,
        "historical_percentile_status": metadata.get("historical_percentile_status") or historical.get("status"),
        "forward_eps": inputs.get("forward_eps") or {},
    }
    return data


def valuation_history(conn: sqlite3.Connection, ticker: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, ticker, market, generated_at, valuation_available, current_price, market_cap,
               pe_ttm, ps_ttm, pb, historical_percentile, peer_comparison_json,
               valuation_status, missing_data_json, allowed_usage, metadata_json,
               ev_ebitda_ttm, peer_set_json, broker_forward_eps_proxy, valuation_confidence
        FROM valuation_snapshot
        WHERE ticker=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (ticker.upper(), max(1, int(limit or 20))),
    ).fetchall()
    return [_decode_valuation_row(row) for row in rows]


def phase11_baseline_valuation(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    snapshots = valuation_history(conn, ticker)
    if not snapshots:
        return latest_valuation_snapshot(conn, ticker)
    latest = snapshots[0]
    latest_peer_count = int(latest.get("peer_count_available") or 0)
    latest_hist_status = latest.get("historical_percentile_status")
    for snapshot in snapshots[1:]:
        peer_count = int(snapshot.get("peer_count_available") or 0)
        hist_status = snapshot.get("historical_percentile_status")
        if peer_count < latest_peer_count or (latest_hist_status in {"available", "partial"} and hist_status == "missing"):
            return snapshot
    return latest


def _decode_fundamentals_row(row: sqlite3.Row) -> dict[str, Any]:
    data = {
        "snapshot_id": row["snapshot_id"],
        "ticker": row["ticker"],
        "market": row["market"],
        "period": row["period"],
        "fiscal_year": row["fiscal_year"],
        "fiscal_quarter": row["fiscal_quarter"],
        "source_evidence_ids": loads(row["source_evidence_ids_json"], []),
        "source_quality": row["source_quality"],
        "freshness_status": row["freshness_status"],
        "confidence": row["confidence"],
        "missing_fields": loads(row["missing_fields_json"], []),
        "field_details": loads(row["field_details_json"], {}),
        "field_missing_reasons": loads(row["field_missing_reasons_json"], {}),
        "created_at": row["created_at"],
        "metadata": loads(row["metadata_json"], {}),
    }
    for field in FUNDAMENTAL_FIELDS:
        data[field] = row[field]
    return data


def fundamentals_history(conn: sqlite3.Connection, ticker: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"""
        SELECT snapshot_id, ticker, market, period, fiscal_year, fiscal_quarter,
               {', '.join(FUNDAMENTAL_FIELDS)},
               source_evidence_ids_json, source_quality, freshness_status, confidence,
               missing_fields_json, field_details_json, field_missing_reasons_json, created_at, metadata_json
        FROM fundamentals_snapshot
        WHERE ticker=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (ticker.upper(), max(1, int(limit or 20))),
    ).fetchall()
    return [_decode_fundamentals_row(row) for row in rows]


def diagnostics_from_fundamentals_snapshot(snapshot: dict[str, Any], ticker: str) -> dict[str, Any]:
    fields = field_quality_from_snapshot(snapshot)
    causes = root_causes_from_field_quality(fields)
    return {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "overall_data_quality_status": data_quality_status(causes),
        "fundamentals_snapshot_id": snapshot.get("snapshot_id"),
        "fundamentals_status": snapshot.get("freshness_status"),
        "root_causes": causes,
        "evidence_issues": [],
        "field_quality": fields,
    }


def phase11_baseline_data_quality(conn: sqlite3.Connection, ticker: str, after_snapshot: dict[str, Any]) -> dict[str, Any]:
    history = fundamentals_history(conn, ticker)
    if not history:
        return build_diagnostics(conn, ticker, refresh_fundamentals=False)
    after_fields = field_quality_from_snapshot(after_snapshot)
    after_missing = {field for field, detail in after_fields.items() if detail.get("status") == "missing"}
    for snapshot in history[1:]:
        fields = field_quality_from_snapshot(snapshot)
        missing = {field for field, detail in fields.items() if detail.get("status") == "missing"}
        if len(missing) > len(after_missing) or ("shareholders_equity" in missing and "shareholders_equity" not in after_missing):
            return diagnostics_from_fundamentals_snapshot(snapshot, ticker)
    return diagnostics_from_fundamentals_snapshot(history[0], ticker)


def valuation_summary(snapshot: dict[str, Any], diagnostics: dict[str, Any] | None = None) -> dict[str, Any]:
    diagnostics = diagnostics or {}
    peer = snapshot.get("peer_comparison") or {}
    historical = snapshot.get("historical_valuation") or {}
    return {
        "allowed_usage": snapshot.get("allowed_usage"),
        "valuation_status": snapshot.get("valuation_status"),
        "price_status": diagnostics.get("price_status") or snapshot.get("price_status"),
        "price_trade_date": snapshot.get("price_trade_date") or (snapshot.get("metadata") or {}).get("price_trade_date"),
        "peer_set_id": snapshot.get("peer_set_id") or peer.get("peer_set_id"),
        "peer_set_status": snapshot.get("peer_set_status") or peer.get("peer_set_status"),
        "peer_count_available": snapshot.get("peer_count_available") or peer.get("peer_count_available"),
        "peer_count_required": snapshot.get("peer_count_required") or peer.get("peer_count_required"),
        "peer_comparison_status": peer.get("peer_comparison_status"),
        "historical_percentile_status": snapshot.get("historical_percentile_status") or historical.get("status"),
        "historical_available_metrics": [
            metric for metric, detail in (historical.get("metrics") or {}).items() if detail.get("status") == "available"
        ],
        "forward_eps_status": (snapshot.get("forward_eps") or {}).get("status") or ("proxy" if snapshot.get("broker_forward_eps_proxy") else "missing"),
        "sub_blockers": diagnostics.get("sub_blockers") or [item["code"] for item in valuation_sub_blockers(snapshot)],
    }


def data_quality_summary(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_keys = root_cause_keys(before.get("root_causes") or [])
    after_keys = root_cause_keys(after.get("root_causes") or [])
    return {
        "before": before.get("overall_data_quality_status"),
        "after": after.get("overall_data_quality_status"),
        "resolved_root_causes": sorted(set(before_keys) - set(after_keys)),
        "remaining_root_causes": after_keys,
        "field_changes": field_changes(before.get("field_quality") or {}, after.get("field_quality") or {}),
    }


def bear_case_update(ticker: str, before_valuation: dict[str, Any], after_valuation: dict[str, Any]) -> dict[str, Any]:
    claim = {"claim_id": "phase11_valuation_rerating", "claim_text": "valuation rerating lacks support", "severity": "high"}
    before = respond_to_bear_case(ticker, {"bear_case_claims": [claim]}, evidence_rows=[], valuation_snapshot=before_valuation)
    after = respond_to_bear_case(ticker, {"bear_case_claims": [claim]}, evidence_rows=[], valuation_snapshot=after_valuation)
    return {
        "before": before.get("overall_response_status"),
        "after": after.get("overall_response_status"),
        "action_effect": after.get("action_effect"),
        "detail": after,
    }


def validation_blockers(after_item: dict[str, Any], valuation: dict[str, Any], diagnostics: dict[str, Any], data_quality: dict[str, Any], bear: dict[str, Any]) -> list[str]:
    blockers = set(blocker_codes(after_item))
    blockers.update(diagnostics.get("sub_blockers") or [item["code"] for item in valuation_sub_blockers(valuation)])
    if data_quality.get("after") == "degraded":
        blockers.add("DATA_QUALITY_RISK")
        for key in data_quality.get("remaining_root_causes") or []:
            blockers.add(str(key).split(":", 1)[0])
    if bear.get("after") == "unresolved":
        blockers.add("HIGH_BEAR_CASE_UNRESOLVED")
    elif bear.get("after") == "partially_mitigated":
        blockers.add("HIGH_BEAR_CASE_PARTIALLY_MITIGATED")
    return sorted(code for code in blockers if code)


def validate_phase11_candidate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    days: int = 365,
    timeout: int = 240,
    run_repairs: bool = False,
) -> dict[str, Any]:
    ticker = ticker.upper()
    before_payload = run_phase6_single(ticker, days, timeout)
    before_item = ticker_result(before_payload, ticker)
    before_valuation = phase11_baseline_valuation(conn, ticker)
    before_diagnostics = diagnose_valuation_snapshot(conn, ticker, before=before_valuation)
    latest_fundamentals = latest_fundamentals_snapshot(conn, ticker)
    before_data_quality = phase11_baseline_data_quality(conn, ticker, latest_fundamentals)

    peer_payload = build_peer_valuation_payload(conn, ticker=ticker, execute=run_repairs, timeout=timeout)
    historical_payload = build_historical_valuation_payload(conn, ticker)
    if run_repairs:
        build_fundamentals_snapshot(conn, ticker, prefer_live=True)
        valuation_repair = repair_valuation_for_ticker(conn, ticker, dry_run=False)
        after_payload = run_phase6_single(ticker, days, timeout)
        after_data_quality = build_diagnostics(conn, ticker, refresh_fundamentals=True)
    else:
        valuation_repair = None
        after_payload = before_payload
        after_data_quality = build_diagnostics(conn, ticker, refresh_fundamentals=False)

    after_item = ticker_result(after_payload, ticker)
    after_valuation = latest_valuation_snapshot(conn, ticker)
    after_diagnostics = diagnose_valuation_snapshot(conn, ticker, before=after_valuation)
    fundamentals = latest_fundamentals_snapshot(conn, ticker)
    dq_summary = data_quality_summary(before_data_quality, after_data_quality)
    bear_update = bear_case_update(ticker, before_valuation, after_valuation)
    remaining = validation_blockers(after_item, after_valuation, after_diagnostics, dq_summary, bear_update)
    before_codes = set(blocker_codes(before_item))
    before_codes.update(before_diagnostics.get("sub_blockers") or [])
    resolution = resolve_tasks(conn, ticker=ticker, validation_blockers=remaining, dry_run=True, limit=30)

    peer_before = int(before_valuation.get("peer_count_available") or 0)
    peer_after = int(peer_payload.get("peer_count_available") or 0)
    historical = historical_payload.get("historical_valuation") or {}
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker,
        "before_status": before_item.get("status") or "unknown",
        "after_status": after_item.get("status") or "unknown",
        "promotion_allowed": bool(after_item.get("promotion_allowed")),
        "peer": {
            "peer_set_id": peer_payload.get("peer_set_id"),
            "peer_count_before": peer_before,
            "peer_count_after": peer_after,
            "peer_count_required": peer_payload.get("peer_count_required"),
            "peer_set_status": peer_payload.get("peer_set_status"),
            "peer_comparison_status": peer_payload.get("peer_comparison_status"),
            "remaining_peer_blockers": peer_payload.get("remaining_peer_blockers") or [],
            "peer_missing_detail": peer_payload.get("peer_missing_detail") or {},
        },
        "historical_valuation": {
            "status": historical.get("status"),
            "available_metrics": historical_payload.get("available_metrics") or [],
            "missing_metrics": historical_payload.get("missing_metrics") or [],
            "remaining_historical_blockers": historical_payload.get("remaining_historical_blockers") or [],
            "historical_fundamentals": historical_payload.get("historical_fundamentals") or [],
        },
        "valuation": valuation_summary(after_valuation, after_diagnostics),
        "valuation_repair": valuation_repair,
        "data_quality": dq_summary,
        "bear_case_response": bear_update,
        "blockers_resolved": sorted(before_codes - set(remaining)),
        "blockers_remaining": remaining,
        "candidate": {
            "action": after_item.get("action"),
            "status": after_item.get("status"),
            "position_size": (after_item.get("portfolio_risk") or {}).get("recommended_position_pct") or 0,
        },
        "fundamentals_snapshot_id": fundamentals.get("snapshot_id"),
        "decision_ledger_written": bool(after_item.get("ledger_written")),
        "repair_resolution": resolution,
        "run_repairs": run_repairs,
        "before_run_id": before_payload.get("run_id"),
        "after_run_id": after_payload.get("run_id"),
    }
    register_snapshot(
        conn,
        entity_type="phase11_peer_historical_repaired_candidate_validation",
        entity_id=ticker,
        status=payload["after_status"],
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 11 peer/historical repaired candidate")
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
        payload = validate_phase11_candidate(
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
    log_run(SCRIPT_NAME, "success", "phase11 peer/historical repaired candidate validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
