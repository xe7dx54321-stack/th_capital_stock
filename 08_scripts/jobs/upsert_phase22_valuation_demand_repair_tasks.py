#!/usr/bin/env python3
"""Convert Phase 22 valuation/demand/proxy blockers into repair tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase22_confirmed_demand_evidence import build_ticker_confirmed_demand
from build_phase22_proxy_strengthening import build_ticker_proxy_strengthening
from smr_agents import DB_PATH
from smr_blocker_repair_queue import repair_id_for, upsert_phase22_valuation_demand_repair_task
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation_gate_v2 import diagnose_valuation_gate_v2
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "upsert_phase22_valuation_demand_repair_tasks.py"

TASK_SOURCES = {
    "CONFIRMED_ORDER_EVIDENCE_MISSING": ["contract announcements", "annual report", "customer order announcement"],
    "TENDER_EVIDENCE_MISSING": ["tender award announcements", "exchange announcements", "procurement platforms"],
    "PROCUREMENT_EVIDENCE_MISSING": ["procurement awards", "customer procurement announcements", "operator procurement portals"],
    "CUSTOMER_CAPEX_EVIDENCE_MISSING": ["customer capex news", "cloud capex reports", "data center buildout announcements"],
    "VALUATION_SUPPORT_WEAK": ["peer valuation data", "historical valuation data", "fundamentals snapshot"],
    "FORWARD_EPS_PROXY_ONLY": ["official consensus source", "independent proxy evidence", "sell-side digest evidence"],
    "PROXY_INDEPENDENT_SOURCE_MISSING": ["filing", "independent news source", "industry data"],
    "DEMAND_VALUATION_LINKAGE_WEAK": ["confirmed demand evidence", "tender/procurement evidence", "customer capex evidence"],
}

VALUATION_BLOCKER_GAPS = {
    "PRICE_STALE",
    "VALUATION_STALE",
    "PEER_COMPARISON_MISSING",
    "PEER_COMPARISON_WEAK",
    "HISTORICAL_VALUATION_MISSING",
    "HISTORICAL_VALUATION_WEAK",
    "VALUATION_EVIDENCE_QUALITY_LOW",
    "VALUATION_CONFIDENCE_LOW",
    "VALUATION_SUPPORTING_ONLY",
    "MARGIN_ASSUMPTION_UNSUPPORTED",
}


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def task_type_for_gap(gap: str, *, gate_type: str) -> str:
    raw = str(gap or "").lower()
    upper = str(gap or "").upper()
    if "forward_eps_proxy_only" in raw or "proxy eps" in raw:
        return "FORWARD_EPS_PROXY_ONLY"
    if upper in VALUATION_BLOCKER_GAPS:
        return "VALUATION_SUPPORT_WEAK"
    if upper in {"DEMAND_ASSUMPTION_UNSUPPORTED", "REVENUE_GROWTH_ASSUMPTION_UNSUPPORTED"}:
        return "DEMAND_VALUATION_LINKAGE_WEAK"
    if "valuation" in raw and "supporting" in raw:
        return "VALUATION_SUPPORT_WEAK"
    if "tender" in raw:
        return "TENDER_EVIDENCE_MISSING"
    if "procurement" in raw:
        return "PROCUREMENT_EVIDENCE_MISSING"
    if "customer capex" in raw or "capex" in raw:
        return "CUSTOMER_CAPEX_EVIDENCE_MISSING"
    if "confirmed" in raw or "signed" in raw or "order" in raw:
        return "CONFIRMED_ORDER_EVIDENCE_MISSING"
    if "independent" in raw or "proxy" in raw:
        return "PROXY_INDEPENDENT_SOURCE_MISSING"
    if gate_type == "VALUATION_GATE":
        return "DEMAND_VALUATION_LINKAGE_WEAK"
    return "CONFIRMED_ORDER_EVIDENCE_MISSING"


def priority_for_task(task_type: str, gate_type: str, status: str | None = None) -> str:
    if task_type in {"CONFIRMED_ORDER_EVIDENCE_MISSING", "TENDER_EVIDENCE_MISSING", "PROCUREMENT_EVIDENCE_MISSING"}:
        return "high"
    if gate_type == "VALUATION_GATE" and str(status or "") in {"context_only", "insufficient", "blocked"}:
        return "high"
    if task_type in {"FORWARD_EPS_PROXY_ONLY", "PROXY_INDEPENDENT_SOURCE_MISSING", "DEMAND_VALUATION_LINKAGE_WEAK"}:
        return "medium"
    return "low"


def stable_blocker_code(task_type: str, gate_type: str, missing_evidence: str) -> str:
    suffix = hashlib.sha1("|".join([gate_type, missing_evidence, task_type]).encode("utf-8")).hexdigest()[:10]
    return f"{task_type}_{suffix}"


def dry_run_task(ticker: str, watchlist: str, *, gate_type: str, missing_evidence: str, status: str | None = None) -> dict[str, Any]:
    task_type = task_type_for_gap(missing_evidence, gate_type=gate_type)
    priority = priority_for_task(task_type, gate_type, status)
    blocker_code = stable_blocker_code(task_type, gate_type, missing_evidence)
    return {
        "repair_task_id": repair_id_for(ticker, blocker_code, watchlist),
        "task_type": task_type,
        "priority": priority,
        "gate_type": gate_type,
        "missing_evidence": missing_evidence,
        "suggested_sources": TASK_SOURCES.get(task_type) or TASK_SOURCES["CONFIRMED_ORDER_EVIDENCE_MISSING"],
        "source_acquisition_plan_status": "available_via_phase23_source_acquisition_plan",
        "status": "open",
    }


def _append_task(tasks: list[dict[str, Any]], seen: set[tuple[str, str, str]], task: dict[str, Any]) -> None:
    key = (str(task.get("task_type")), str(task.get("gate_type")), str(task.get("missing_evidence")))
    if key in seen:
        return
    seen.add(key)
    tasks.append(task)


def ticker_tasks(conn: sqlite3.Connection, ticker: str, *, watchlist: str, execute: bool) -> dict[str, Any]:
    valuation = diagnose_valuation_gate_v2(conn, ticker, watchlist_id=watchlist).get("valuation_gate_v2") or {}
    confirmed = build_ticker_confirmed_demand(conn, ticker).get("confirmed_demand_evidence") or {}
    proxy = build_ticker_proxy_strengthening(conn, ticker, watchlist=watchlist).get("proxy_strengthening") or {}
    tasks: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for blocker in valuation.get("remaining_blockers") or []:
        _append_task(
            tasks,
            seen,
            dry_run_task(ticker, watchlist, gate_type="VALUATION_GATE", missing_evidence=str(blocker), status=valuation.get("after_status")),
        )
    if (confirmed.get("confirmed_order_count") or 0) == 0:
        reason = confirmed.get("no_confirmed_order_reason") or "confirmed order evidence missing"
        _append_task(tasks, seen, dry_run_task(ticker, watchlist, gate_type="DEMAND_EVIDENCE_GATE", missing_evidence=reason))
        if (confirmed.get("tender_or_procurement_count") or 0) == 0:
            _append_task(tasks, seen, dry_run_task(ticker, watchlist, gate_type="DEMAND_EVIDENCE_GATE", missing_evidence="tender or procurement evidence missing"))
    if ((proxy.get("after") or {}).get("independent_source_count") or 0) < 2:
        _append_task(tasks, seen, dry_run_task(ticker, watchlist, gate_type="PROXY_SIGNAL_GATE", missing_evidence="proxy independent source count < 2"))
    for requirement in proxy.get("remaining_requirements") or []:
        if "proxy_not_official_consensus" in str(requirement):
            continue
        _append_task(tasks, seen, dry_run_task(ticker, watchlist, gate_type="PROXY_SIGNAL_GATE", missing_evidence=str(requirement)))
    if execute:
        for task in tasks:
            stored = upsert_phase22_valuation_demand_repair_task(
                conn,
                ticker=ticker,
                watchlist_id=watchlist,
                task_type=task["task_type"],
                priority=task["priority"],
                gate_type=task["gate_type"],
                missing_evidence=task["missing_evidence"],
                suggested_sources=task["suggested_sources"],
                source_run_ids=[SCRIPT_NAME],
            )
            task["repair_task_id"] = stored.get("repair_id") or task["repair_task_id"]
            task["status"] = stored.get("status") or "open"
    return {"ticker": ticker, "tasks_upserted" if execute else "tasks_preview": tasks}


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str, execute: bool) -> dict[str, Any]:
    rows = [ticker_tasks(conn, ticker, watchlist=watchlist, execute=execute) for ticker in tickers]
    key = "tasks_upserted" if execute else "tasks_preview"
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "mode": "execute" if execute else "dry_run",
        "summary": {
            "tickers_checked": len(rows),
            "tasks_identified": sum(len(row.get(key) or []) for row in rows),
            "tasks_written": sum(len(row.get("tasks_upserted") or []) for row in rows) if execute else 0,
        },
        "ticker_results": rows,
        "safety": {
            "dry_run_no_write": not execute,
            "promotion_rules_relaxed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upsert Phase 22 valuation/demand repair tasks")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.dry_run and args.execute:
        raise SystemExit("Use only one of --dry-run or --execute")
    execute = bool(args.execute)
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(
            conn,
            parse_tickers(args.tickers, args.watchlist if not args.tickers else None),
            watchlist=args.watchlist,
            execute=execute,
        )
        register_snapshot(
            conn,
            entity_type="phase22_valuation_demand_repair_tasks",
            entity_id=args.tickers or args.watchlist,
            status="executed" if execute else "dry_run",
            source=SCRIPT_NAME,
            payload=payload,
        )
        if execute:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase22 repair task upsert complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
