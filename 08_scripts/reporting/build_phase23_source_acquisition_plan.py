#!/usr/bin/env python3
"""Build Phase 23 source acquisition plans from Phase 22 repair tasks."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_agents import DB_PATH
from smr_phase6_watchlists import load_watchlist_config, watchlist_map
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_source_acquisition_plan import build_source_acquisition_plan_for_task
from smr_source_connector_registry import infer_market_from_ticker
from smr_wiki import now_ts
from upsert_phase22_valuation_demand_repair_tasks import ticker_tasks

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase23_source_acquisition_plan.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _market_for(ticker: str, watchlist: str) -> str:
    item = watchlist_map(watchlist).get(ticker.upper()) or {}
    return infer_market_from_ticker(ticker, item.get("market"))


def build_ticker_payload(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict:
    market = _market_for(ticker, watchlist)
    tasks = ticker_tasks(conn, ticker, watchlist=watchlist, execute=False).get("tasks_preview") or []
    plans = [
        build_source_acquisition_plan_for_task(task, ticker=ticker, market=market)
        for task in tasks
    ]
    return {
        "ticker": ticker.upper(),
        "market": market,
        "repair_tasks": plans,
        "next_actions": [((plan.get("source_acquisition_plan") or {}).get("next_action")) for plan in plans][:8],
        "safety": {
            "planned_connectors_executed": False,
            "writes_evidence_graph": False,
            "promotion_rules_relaxed": False,
        },
    }


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    rows = [build_ticker_payload(conn, ticker, watchlist=watchlist) for ticker in parse_tickers(tickers, watchlist)]
    plans = [plan for row in rows for plan in row.get("repair_tasks") or []]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "repair_tasks_checked": len(plans),
            "acquisition_plans_generated": len(plans),
            "planned_connectors_executed": 0,
            "evidence_graph_writes": 0,
        },
        "ticker_results": rows,
        "safety": {
            "planned_connectors_executed": False,
            "writes_evidence_graph": False,
            "promotion_rules_relaxed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 23 source acquisition plan")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase23_source_acquisition_plan",
            entity_id=args.tickers or args.watchlist,
            status="planned",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase23 source acquisition plan built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
