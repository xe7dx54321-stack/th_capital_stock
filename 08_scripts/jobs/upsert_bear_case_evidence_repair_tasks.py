#!/usr/bin/env python3
"""Convert Phase 21 missing bear-case/proxy evidence into repair tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_bear_case_mitigation import build_ticker_bear_case_mitigation
from smr_blocker_repair_queue import repair_id_for, upsert_phase21_evidence_repair_task
from smr_phase6_watchlists import load_watchlist_config
from smr_proxy_signal_gate import build_proxy_signal_gate
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "upsert_bear_case_evidence_repair_tasks.py"


TASK_SOURCES = {
    "DIRECT_DEMAND_EVIDENCE_MISSING": ["annual report", "latest news", "customer capex news", "procurement/tender announcements"],
    "ORDER_EVIDENCE_MISSING": ["contract announcements", "tender/procurement announcements", "annual report"],
    "CUSTOMER_EVIDENCE_MISSING": ["customer announcements", "investor relations records", "latest news"],
    "DOWNSTREAM_CAPEX_EVIDENCE_MISSING": ["cloud capex news", "data center procurement news", "operator capex filings"],
    "PROXY_INDEPENDENT_SOURCE_MISSING": ["independent news source", "filing", "industry data"],
    "DOMINANT_PROXY_SIGNAL_MISSING": ["proxy extraction evidence", "filing/news support"],
    "CLAIM_GRAPH_SUPPORT_MISSING": ["claim graph evidence", "filing excerpts"],
    "FILING_OR_NEWS_SUPPORT_MISSING": ["annual report", "earnings release", "latest news"],
}


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def task_type_for_missing(text: str) -> str:
    raw = str(text or "").lower()
    if "order" in raw or "订单" in raw or "signed" in raw or "tender" in raw or "procurement" in raw:
        return "ORDER_EVIDENCE_MISSING"
    if "customer" in raw or "客户" in raw:
        return "CUSTOMER_EVIDENCE_MISSING"
    if "capex" in raw or "data center" in raw or "cloud" in raw:
        return "DOWNSTREAM_CAPEX_EVIDENCE_MISSING"
    if "independent" in raw or "second independent" in raw:
        return "PROXY_INDEPENDENT_SOURCE_MISSING"
    if "dominant_proxy_signal" in raw or "proxy" in raw:
        return "DOMINANT_PROXY_SIGNAL_MISSING"
    if "claim graph" in raw:
        return "CLAIM_GRAPH_SUPPORT_MISSING"
    if "filing" in raw or "news" in raw:
        return "FILING_OR_NEWS_SUPPORT_MISSING"
    return "DIRECT_DEMAND_EVIDENCE_MISSING"


def priority_for_response(response: dict[str, Any]) -> str:
    if response.get("core_to_thesis") and response.get("residual_risk_level") in {"high", "critical"}:
        return "high"
    if response.get("core_to_thesis"):
        return "medium"
    return "low"


def stable_blocker_code(task_type: str, claim_id: str, missing_evidence: str) -> str:
    suffix = hashlib.sha1("|".join([str(claim_id or ""), str(missing_evidence or "")]).encode("utf-8")).hexdigest()[:10]
    return f"{task_type}_{suffix}"


def dry_run_task(ticker: str, watchlist: str, response: dict[str, Any], missing: str) -> dict[str, Any]:
    task_type = task_type_for_missing(missing)
    claim_id = str(response.get("bear_case_claim_id") or "bear_case_missing_evidence")
    blocker_code = stable_blocker_code(task_type, claim_id, missing)
    return {
        "repair_task_id": repair_id_for(ticker, blocker_code, watchlist),
        "task_type": task_type,
        "priority": priority_for_response(response),
        "source_bear_case_claim_id": claim_id,
        "missing_evidence": missing,
        "suggested_sources": TASK_SOURCES.get(task_type) or TASK_SOURCES["DIRECT_DEMAND_EVIDENCE_MISSING"],
        "status": "open",
        "gate_type": "BEAR_CASE_GATE",
    }


def ticker_tasks(conn: sqlite3.Connection, ticker: str, *, watchlist: str, execute: bool) -> dict[str, Any]:
    mitigation = build_ticker_bear_case_mitigation(conn, ticker, watchlist_id=watchlist)
    tasks: list[dict[str, Any]] = []
    seen = set()
    for response in (mitigation.get("bear_case_mitigation") or {}).get("responses") or []:
        for missing in response.get("missing_evidence") or []:
            task = dry_run_task(ticker, watchlist, response, str(missing))
            key = (task["task_type"], task["source_bear_case_claim_id"], task["missing_evidence"])
            if key in seen:
                continue
            seen.add(key)
            if execute:
                stored = upsert_phase21_evidence_repair_task(
                    conn,
                    ticker=ticker,
                    watchlist_id=watchlist,
                    task_type=task["task_type"],
                    priority=task["priority"],
                    source_bear_case_claim_id=task["source_bear_case_claim_id"],
                    missing_evidence=task["missing_evidence"],
                    suggested_sources=task["suggested_sources"],
                    gate_type="BEAR_CASE_GATE",
                    source_run_ids=[SCRIPT_NAME],
                )
                task["repair_task_id"] = stored.get("repair_id") or task["repair_task_id"]
                task["status"] = stored.get("status") or "open"
            tasks.append(task)
    proxy_gate = build_proxy_signal_gate(conn, ticker, watchlist_id=watchlist).get("proxy_signal_gate") or {}
    if proxy_gate.get("status") in {"weak", "missing", "invalid", "conflicted"}:
        response = {
            "bear_case_claim_id": "proxy_signal_gate",
            "core_to_thesis": True,
            "residual_risk_level": "high",
        }
        for missing in proxy_gate.get("missing_requirements") or []:
            task = dry_run_task(ticker, watchlist, response, str(missing))
            task["gate_type"] = "PROXY_SIGNAL_GATE"
            if execute:
                stored = upsert_phase21_evidence_repair_task(
                    conn,
                    ticker=ticker,
                    watchlist_id=watchlist,
                    task_type=task["task_type"],
                    priority=task["priority"],
                    source_bear_case_claim_id=task["source_bear_case_claim_id"],
                    missing_evidence=task["missing_evidence"],
                    suggested_sources=task["suggested_sources"],
                    gate_type="PROXY_SIGNAL_GATE",
                    source_run_ids=[SCRIPT_NAME],
                )
                task["repair_task_id"] = stored.get("repair_id") or task["repair_task_id"]
                task["status"] = stored.get("status") or "open"
            tasks.append(task)
    return {
        "ticker": ticker,
        "tasks_upserted" if execute else "tasks_preview": tasks,
    }


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
    parser = argparse.ArgumentParser(description="Upsert Phase 21 bear-case evidence repair tasks")
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
    tickers = parse_tickers(args.tickers, args.watchlist if not args.tickers else None)
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers, watchlist=args.watchlist, execute=execute)
        register_snapshot(
            conn,
            entity_type="phase21_bear_case_evidence_repair_tasks",
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
    log_run(SCRIPT_NAME, "success", "phase21 repair task upsert complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
