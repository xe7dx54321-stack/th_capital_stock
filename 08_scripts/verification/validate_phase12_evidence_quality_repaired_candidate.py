#!/usr/bin/env python3
"""Phase 12 validation for A/H evidence quality and field confidence hardening."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, JOBS_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase12_data_quality_before_after import build_phase12_data_quality_report
from run_phase10_repair_resolution import resolve_tasks
from smr_agents import DB_PATH
from smr_bear_case_response import respond_to_bear_case
from smr_fundamentals import latest_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import diagnose_valuation_snapshot, latest_valuation_snapshot, valuation_sub_blockers
from smr_wiki import now_ts
from validate_phase11_peer_historical_repaired_candidate import (
    blocker_codes,
    run_phase6_single,
    ticker_result,
    valuation_summary,
)


SCRIPT_NAME = "validate_phase12_evidence_quality_repaired_candidate.py"


def _root_code_set(root_causes: list[str]) -> list[str]:
    return sorted({str(item).split(":", 1)[0] for item in root_causes if item})


def _field_quality_delta(report: dict[str, Any]) -> dict[str, Any]:
    before_fields = report.get("before_field_quality") or {}
    after_fields = report.get("after_field_quality") or {}
    promoted: list[str] = []
    context_only: list[str] = []
    blocked: list[str] = []
    for field, detail in after_fields.items():
        before_usage = (before_fields.get(field) or {}).get("allowed_usage")
        after_usage = detail.get("allowed_usage")
        if after_usage in {"supporting_evidence", "promotion_evidence"} and before_usage not in {
            "supporting_evidence",
            "promotion_evidence",
        }:
            promoted.append(field)
        if after_usage == "context_only":
            context_only.append(field)
        if after_usage == "blocked":
            blocked.append(field)
    return {
        "fields_promoted_to_supporting": sorted(promoted),
        "fields_still_context_only": sorted(context_only),
        "fields_blocked": sorted(blocked),
        "source_evidence_field_count": (report.get("improvement_summary") or {}).get("fields_with_source_evidence_after", 0),
    }


def bear_case_response_v3(
    ticker: str,
    before_fundamentals: dict[str, Any],
    after_fundamentals: dict[str, Any],
    valuation: dict[str, Any],
) -> dict[str, Any]:
    claims = [
        {
            "claim_id": "bear_valuation_001",
            "claim_text": "valuation support is insufficient",
            "severity": "high",
        },
        {
            "claim_id": "bear_quality_001",
            "claim_text": "fundamentals data quality remains weak",
            "severity": "high",
        },
    ]
    before = respond_to_bear_case(
        ticker,
        {"bear_case_claims": claims},
        fundamentals_snapshot=before_fundamentals,
        valuation_snapshot=valuation,
    )
    after = respond_to_bear_case(
        ticker,
        {"bear_case_claims": claims},
        fundamentals_snapshot=after_fundamentals,
        valuation_snapshot=valuation,
    )
    return {
        "before": before.get("overall_response_status"),
        "after": after.get("overall_response_status"),
        "action_effect": after.get("action_effect"),
        "detail": after,
        "responses": after.get("responses") or [],
    }


def validation_blockers(
    after_item: dict[str, Any],
    valuation: dict[str, Any],
    valuation_diagnostics: dict[str, Any],
    data_quality: dict[str, Any],
    bear_case: dict[str, Any],
) -> list[str]:
    blockers = set(blocker_codes(after_item))
    blockers.update(valuation_diagnostics.get("sub_blockers") or [item["code"] for item in valuation_sub_blockers(valuation)])
    remaining_roots = data_quality.get("remaining_root_causes") or []
    if remaining_roots:
        blockers.add("DATA_QUALITY_RISK")
        blockers.update(_root_code_set(remaining_roots))
    if bear_case.get("after") == "unresolved":
        blockers.add("HIGH_BEAR_CASE_UNRESOLVED")
    elif bear_case.get("after") == "partially_mitigated":
        blockers.add("HIGH_BEAR_CASE_PARTIALLY_MITIGATED")
    return sorted(code for code in blockers if code)


def validate_phase12_candidate(
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
    before_fundamentals = latest_fundamentals_snapshot(conn, ticker)
    before_valuation = latest_valuation_snapshot(conn, ticker)

    data_quality_report = build_phase12_data_quality_report(conn, ticker, refresh_fundamentals=True)
    after_fundamentals = latest_fundamentals_snapshot(conn, ticker)
    after_valuation = latest_valuation_snapshot(conn, ticker)
    after_diagnostics = diagnose_valuation_snapshot(conn, ticker, before=after_valuation)
    after_payload = run_phase6_single(ticker, days, timeout)
    after_item = ticker_result(after_payload, ticker)

    bear_update = bear_case_response_v3(ticker, before_fundamentals, after_fundamentals, after_valuation)
    data_quality = {
        "before": (data_quality_report.get("before") or {}).get("data_quality_status"),
        "after": (data_quality_report.get("after") or {}).get("data_quality_status"),
        "resolved_root_causes": data_quality_report.get("resolved_root_causes") or [],
        "remaining_root_causes": data_quality_report.get("remaining_root_causes") or [],
        "resolved_root_cause_codes": data_quality_report.get("resolved_root_cause_codes") or [],
        "improvement_summary": data_quality_report.get("improvement_summary") or {},
    }
    remaining = validation_blockers(after_item, after_valuation, after_diagnostics, data_quality, bear_update)
    before_codes = set(blocker_codes(before_item))
    before_codes.update(_root_code_set((data_quality_report.get("before") or {}).get("root_causes") or []))
    before_codes.update(str(code) for code in (after_diagnostics.get("sub_blockers") or []) if code)
    resolution = resolve_tasks(conn, ticker=ticker, validation_blockers=remaining, dry_run=not run_repairs, limit=30)
    field_quality = _field_quality_delta(data_quality_report)
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker,
        "before_status": before_item.get("status") or "unknown",
        "after_status": after_item.get("status") or "unknown",
        "promotion_allowed": bool(after_item.get("promotion_allowed")),
        "data_quality": data_quality,
        "field_quality": field_quality,
        "valuation": valuation_summary(after_valuation, after_diagnostics),
        "bear_case_response": {
            "before": bear_update.get("before"),
            "after": bear_update.get("after"),
            "action_effect": bear_update.get("action_effect"),
            "responses": bear_update.get("responses") or [],
        },
        "blockers_resolved": sorted(code for code in before_codes - set(remaining) if code),
        "blockers_remaining": remaining,
        "candidate": {
            "action": after_item.get("action"),
            "status": after_item.get("status"),
            "position_size": (after_item.get("portfolio_risk") or {}).get("recommended_position_pct") or 0,
        },
        "fundamentals_snapshot_id": after_fundamentals.get("snapshot_id"),
        "decision_ledger_written": bool(after_item.get("ledger_written")),
        "repair_resolution": resolution,
        "run_repairs": run_repairs,
        "before_run_id": before_payload.get("run_id"),
        "after_run_id": after_payload.get("run_id"),
    }
    register_snapshot(
        conn,
        entity_type="phase12_evidence_quality_repaired_candidate_validation",
        entity_id=ticker,
        status=payload["after_status"],
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 12 A/H evidence-quality repaired candidate")
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
        payload = validate_phase12_candidate(
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
    log_run(SCRIPT_NAME, "success", "phase12 evidence quality repaired candidate validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
