#!/usr/bin/env python3
"""Diagnostics for stale data sources and repair recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smr_data_health import get_system_data_health
from smr_paths import project_path

RUN_LOG_PATH = project_path("10_logs", "script_runs.jsonl")

DAILY_BAR_SCRIPTS = {
    "A": ["ah_daily_bar.py", "market_data_harvest"],
    "H": ["ah_daily_bar.py", "market_data_harvest"],
    "US": ["ah_daily_bar.py", "market_data_harvest"],
}

FILINGS_SCRIPTS = [
    "fetch_cninfo_announcements.py",
    "fetch_hkex_announcements.py",
    "fetch_sec_official_materials.py",
    "fetch_ir_primary_materials.py",
    "normalize_market_events.py",
]


def load_recent_run_logs(path: Path | None = None, limit: int = 1000) -> list[dict[str, Any]]:
    path = path or RUN_LOG_PATH
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    rows = []
    for line in lines:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def latest_run(logs: list[dict[str, Any]], scripts: list[str]) -> dict[str, Any] | None:
    script_set = {item for item in scripts if item}
    for row in reversed(logs):
        script = str(row.get("script") or "")
        if script in script_set or any(script.endswith(f"/{item}") for item in script_set):
            return row
    return None


def probable_cause(row: dict[str, Any], run: dict[str, Any] | None) -> str:
    status = row.get("freshness_status")
    metadata = row.get("metadata") or {}
    if status == "fresh":
        return "none"
    missing = metadata.get("missing_sessions") or []
    if row.get("data_type") == "daily_bar" and not missing and status in {"stale", "missing"}:
        return "market_calendar_mismatch"
    if not run:
        return "job_not_scheduled"
    run_status = str(run.get("status") or "").lower()
    message = str(run.get("message") or "").lower()
    metrics = run.get("metrics") or {}
    if run_status not in {"success", "ok", "partial"}:
        if "auth" in message or "key" in message or "token" in message:
            return "api_auth_failed"
        if "rate" in message or "limit" in message:
            return "api_rate_limited"
        if "timeout" in message:
            return "job_failed"
        return "job_failed"
    if status in {"stale", "missing"} and metrics.get("inserted_count") == 0:
        return "empty_vendor_response"
    if status in {"stale", "missing"}:
        return "write_failed_or_health_not_recomputed"
    return "unknown"


def repair_action(row: dict[str, Any]) -> str | None:
    data_type = row.get("data_type")
    market = row.get("market")
    if data_type == "daily_bar":
        return f"python3 08_scripts/jobs/repair_daily_bar_backfill.py --market {market}"
    if data_type == "filings":
        return "python3 08_scripts/jobs/repair_filings_ingestion.py"
    if data_type in {"news", "fundamentals", "consensus_revision"}:
        return "python3 08_scripts/jobs/recompute_data_source_health.py"
    return None


def diagnose_data_freshness(conn, refresh: bool = True) -> list[dict[str, Any]]:
    snapshot = get_system_data_health(conn, refresh=refresh)
    logs = load_recent_run_logs()
    diagnostics = []
    for item in snapshot.get("items") or []:
        data_type = item.get("data_type")
        market = item.get("market")
        if data_type == "daily_bar":
            scripts = DAILY_BAR_SCRIPTS.get(str(market), ["ah_daily_bar.py"])
        elif data_type == "filings":
            scripts = FILINGS_SCRIPTS
        else:
            scripts = [str(item.get("source_key") or data_type)]
        run = latest_run(logs, scripts)
        metadata = item.get("metadata") or {}
        diagnostics.append(
            {
                "source_key": item.get("source_key"),
                "market": market,
                "data_type": data_type,
                "health_status": item.get("freshness_status"),
                "blocking_level": item.get("blocking_level"),
                "last_job_run_at": run.get("time") if run else None,
                "last_job_status": run.get("status") if run else None,
                "last_error": run.get("message") if run and str(run.get("status") or "").lower() not in {"success", "ok"} else None,
                "last_success_at": item.get("last_success_at"),
                "last_data_timestamp": item.get("last_data_timestamp"),
                "expected_latest_trading_day": metadata.get("expected_latest_trading_day"),
                "actual_latest_trading_day": metadata.get("actual_latest_trading_day"),
                "missing_sessions": metadata.get("missing_sessions") or [],
                "probable_cause": probable_cause(item, run),
                "recommended_repair_action": repair_action(item),
                "staleness_reason": item.get("staleness_reason"),
            }
        )
    return diagnostics
