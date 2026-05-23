#!/usr/bin/env python3
"""Phase 8 A/H candidate recovery validator.

Default target is 09988.HK. The script does not relax promotion rules; it
reruns the live single-ticker pipeline, then makes the recovery gap explicit.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_blocker_repair_queue import list_repair_tasks, upsert_repair_task
from smr_blocker_taxonomy import minimum_fix_path_from_blockers, normalize_blocker, normalize_blockers, priority_for_blocker
from smr_fundamentals import FUNDAMENTAL_FIELDS, ensure_fundamentals_tables, latest_fundamentals_snapshot
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase8_ah_candidate_recovery.py"
CORE_RECOVERY_FIELDS = [
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "eps_basic",
    "eps_diluted",
    "operating_cash_flow",
    "capex",
    "free_cash_flow",
    "cash_and_equivalents",
    "total_debt",
    "shareholders_equity",
]


def market_for_ticker(ticker: str | None) -> str:
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "HK"
    return "US"


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


def field_extraction_from_snapshot(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details = snapshot.get("field_details") or {}
    missing_reasons = snapshot.get("field_missing_reasons") or {}
    result: dict[str, dict[str, Any]] = {}
    for field in CORE_RECOVERY_FIELDS:
        detail = dict(details.get(field) or {})
        value = detail.get("extracted_value")
        if value is None and snapshot.get(field) is not None:
            value = snapshot.get(field)
            detail["extracted_value"] = value
        missing_reason = detail.get("missing_reason") or missing_reasons.get(field)
        status = "extracted" if value is not None and missing_reason in {None, "", "null"} else "missing"
        result[field] = {
            "status": status,
            "extracted_value": value,
            "unit": detail.get("unit"),
            "currency": detail.get("currency"),
            "period": detail.get("period") or snapshot.get("period"),
            "source_evidence_id": detail.get("source_evidence_id"),
            "confidence": detail.get("confidence") if detail.get("confidence") is not None else 0.0,
            "missing_reason": None if status == "extracted" else (missing_reason or "field_not_found"),
            "warnings": detail.get("warnings") or [],
        }
    return result


def recovery_blockers(ticker_result: dict[str, Any], snapshot: dict[str, Any], field_extraction: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = normalize_blockers(
        ticker_result.get("blocking_factors") or (ticker_result.get("promotion_debugger") or {}).get("blocking_factors") or [],
        context={
            "proxy_quality": ticker_result.get("proxy_quality"),
            "fundamentals_missing_fields": ticker_result.get("fundamentals_missing_fields") or snapshot.get("missing_fields") or [],
        },
    )
    missing_fields = [field for field, detail in field_extraction.items() if detail.get("status") == "missing"]
    if missing_fields and not any(item.get("code") == "FUNDAMENTALS_MISSING_FIELDS" for item in blockers):
        blockers.append(
            normalize_blocker(
                {
                    "code": "FUNDAMENTALS_MISSING_FIELDS",
                    "affected_fields": missing_fields,
                    "message": "field-level A/H fundamentals still have missing values",
                    "suggested_fix": "extend HKEX/CN financial field synonym map and cash-flow/balance-sheet parsing",
                },
                context={"fundamentals_missing_fields": missing_fields},
            )
        )
    if ticker_result.get("proxy_quality") in {None, "invalid"} and not any(item.get("code") == "PROXY_INVALID" for item in blockers):
        blockers.append(normalize_blocker({"code": "PROXY_INVALID", "message": "proxy quality is invalid or missing"}))
    if ticker_result.get("valuation_usage") in {"context_only", None} and not any(item.get("code", "").startswith("VALUATION") for item in blockers):
        blockers.append(normalize_blocker({"code": "VALUATION_CONTEXT_ONLY", "message": "valuation is not promotion-grade"}))
    return blockers


def upsert_recovery_tasks(
    conn: sqlite3.Connection,
    ticker: str,
    market: str,
    blockers: list[dict[str, Any]],
    run_id: str | None,
    current_status: str | None,
) -> list[dict[str, Any]]:
    tasks = []
    for blocker in blockers:
        task = upsert_repair_task(
            conn,
            ticker=ticker,
            market=market,
            watchlist_id="ai_core",
            blocker_code=blocker["code"],
            blocker_type=blocker.get("type"),
            priority=priority_for_blocker(blocker),
            severity=blocker.get("severity"),
            fixability=blocker.get("fixability"),
            expected_impact=blocker.get("expected_impact"),
            suggested_fix=blocker.get("suggested_fix"),
            source_run_ids=[run_id] if run_id else [],
            affected_fields=blocker.get("affected_fields") or [],
            metadata={
                "source": SCRIPT_NAME,
                "current_status": current_status,
                "target_status": "pending_human_review",
            },
        )
        tasks.append(task)
    return tasks


def build_payload(
    *,
    ticker: str,
    phase6_payload: dict[str, Any],
    fundamentals_snapshot: dict[str, Any],
    repair_tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ticker_result = {}
    for item in phase6_payload.get("tickers") or []:
        if str(item.get("ticker") or "").upper() == ticker.upper():
            ticker_result = item
            break
    field_extraction = field_extraction_from_snapshot(fundamentals_snapshot)
    blockers = recovery_blockers(ticker_result, fundamentals_snapshot, field_extraction)
    status = ticker_result.get("status") or "unknown"
    promotion_allowed = bool(ticker_result.get("promotion_allowed"))
    pending_with_live = status == "pending_human_review" and (
        int(ticker_result.get("live_filing_evidence") or 0) > 0 or int(ticker_result.get("live_news_evidence") or 0) > 0
    )
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "market": market_for_ticker(ticker),
        "current_status": status,
        "target_status": "pending_human_review",
        "promotion_allowed": promotion_allowed,
        "live_evidence_used": pending_with_live,
        "live_news_evidence": ticker_result.get("live_news_evidence"),
        "live_filing_evidence": ticker_result.get("live_filing_evidence"),
        "proxy_quality": ticker_result.get("proxy_quality"),
        "valuation_usage": ticker_result.get("valuation_usage"),
        "fundamentals_status": fundamentals_snapshot.get("freshness_status") or ticker_result.get("fundamentals_status"),
        "field_extraction": field_extraction,
        "blocking_factors": blockers,
        "minimum_fix_path": minimum_fix_path_from_blockers(blockers),
        "promotion_gap": {
            "missing_requirements": ticker_result.get("missing_requirements") or [],
            "required_fixes": ticker_result.get("required_fixes") or [],
            "candidate_action": ticker_result.get("action"),
        },
        "phase6_run_id": phase6_payload.get("run_id"),
        "phase6_summary": phase6_payload.get("summary") or {},
        "repair_tasks_created": len(repair_tasks or []),
        "repair_tasks": repair_tasks or [],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 8 A/H Candidate Recovery",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- ticker: `{payload.get('ticker')}`",
        f"- market: `{payload.get('market')}`",
        f"- current_status: `{payload.get('current_status')}`",
        f"- target_status: `{payload.get('target_status')}`",
        f"- promotion_allowed: `{payload.get('promotion_allowed')}`",
        f"- proxy_quality: `{payload.get('proxy_quality')}`",
        f"- valuation_usage: `{payload.get('valuation_usage')}`",
        f"- fundamentals_status: `{payload.get('fundamentals_status')}`",
        f"- repair_tasks_created: `{payload.get('repair_tasks_created')}`",
        "",
        "## Field Extraction",
        "",
        "| Field | Status | Value | Unit | Confidence | Missing Reason | Evidence |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for field, detail in payload.get("field_extraction", {}).items():
        lines.append(
            "| {field} | {status} | {value} | {unit} | {confidence} | {reason} | {evidence} |".format(
                field=field,
                status=detail.get("status"),
                value=detail.get("extracted_value") if detail.get("extracted_value") is not None else "-",
                unit=detail.get("unit") or "-",
                confidence=detail.get("confidence") or 0.0,
                reason=detail.get("missing_reason") or "-",
                evidence=detail.get("source_evidence_id") or "-",
            )
        )
    lines.extend(["", "## Blocking Factors", "", "| Code | Severity | Affected Fields | Suggested Fix |", "|---|---|---|---|"])
    for blocker in payload.get("blocking_factors") or []:
        lines.append(
            f"| {blocker.get('code')} | {blocker.get('severity')} | {', '.join(blocker.get('affected_fields') or []) or '-'} | {blocker.get('suggested_fix') or '-'} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 8 A/H candidate recovery")
    parser.add_argument("--ticker", default="09988.HK")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--upsert-repair-queue", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()

    phase6_script = Path(__file__).with_name("validate_phase6_multi_ticker_live.py")
    command = [
        sys.executable,
        str(phase6_script),
        "--tickers",
        args.ticker,
        "--days",
        str(args.days),
        "--timeout",
        str(args.timeout),
    ]
    if args.skip_fetch:
        command.append("--skip-fetch")
    phase6_run = run_command(command, timeout=args.timeout + 30)
    phase6_payload = parse_json_stdout(phase6_run)
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        ensure_fundamentals_tables(conn)
        snapshot = latest_fundamentals_snapshot(conn, args.ticker)
        if not snapshot:
            snapshot = {"ticker": args.ticker, "freshness_status": "missing", "field_details": {}, "field_missing_reasons": {field: "table_not_found" for field in FUNDAMENTAL_FIELDS}}
        provisional = build_payload(ticker=args.ticker, phase6_payload=phase6_payload, fundamentals_snapshot=snapshot)
        repair_tasks = []
        if args.upsert_repair_queue:
            repair_tasks = upsert_recovery_tasks(
                conn,
                args.ticker.upper(),
                market_for_ticker(args.ticker),
                provisional.get("blocking_factors") or [],
                provisional.get("phase6_run_id"),
                provisional.get("current_status"),
            )
        payload = build_payload(ticker=args.ticker, phase6_payload=phase6_payload, fundamentals_snapshot=snapshot, repair_tasks=repair_tasks)
        if args.upsert_repair_queue:
            payload["open_repair_task_count"] = len(list_repair_tasks(conn, status="open", ticker=args.ticker.upper(), watchlist_id="ai_core", limit=100))
        output_dir = project_path("06_reports", "adhoc", "phase8")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{payload['generated_at'][:10]}_{args.ticker.replace('.', '_')}_ah_candidate_recovery.md"
        output_path.write_text(render_markdown(payload), encoding="utf-8")
        register_snapshot(
            conn,
            entity_type="phase8_ah_candidate_recovery",
            entity_id=args.ticker.upper(),
            status=payload.get("current_status") or "unknown",
            source=SCRIPT_NAME,
            payload={**payload, "phase6_run": {k: v for k, v in phase6_run.items() if k != "stdout"}, "summary_rel_path": str(output_path)},
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase8 ah candidate recovery complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
