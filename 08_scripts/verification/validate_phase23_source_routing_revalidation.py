#!/usr/bin/env python3
"""Validate Phase 23 source routing coverage."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase23_demand_source_routing import build_ticker_payload as build_demand_routing
from build_phase23_source_acquisition_plan import build_ticker_payload as build_acquisition_plan
from build_phase23_valuation_source_routing import build_ticker_payload as build_valuation_routing
from smr_agents import DB_PATH
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "validate_phase23_source_routing_revalidation.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _route_counts(routes: list[dict]) -> dict:
    return {
        "implemented": sum(1 for route in routes if route.get("route_status") == "implemented"),
        "partial": sum(1 for route in routes if route.get("route_status") == "partial"),
        "planned": sum(1 for route in routes if route.get("route_status") == "planned_only"),
        "unknown": sum(1 for route in routes if route.get("route_status") == "UNKNOWN_INFORMATION_ROUTE"),
    }


def build_ticker_result(conn: sqlite3.Connection, ticker: str, *, watchlist: str) -> dict:
    valuation = build_valuation_routing(conn, ticker, watchlist=watchlist)
    demand = build_demand_routing(conn, ticker, watchlist=watchlist)
    acquisition = build_acquisition_plan(conn, ticker, watchlist=watchlist)
    all_routes = list(valuation.get("source_routes") or []) + list(demand.get("source_routes") or [])
    counts = _route_counts(all_routes)
    blockers_checked = len(valuation.get("valuation_blockers") or []) + len(demand.get("demand_blockers") or [])
    return {
        "ticker": ticker.upper(),
        "blockers_checked": blockers_checked,
        "blockers_with_routes": blockers_checked - counts["unknown"],
        "blockers_without_routes": counts["unknown"],
        "implemented_route_count": counts["implemented"],
        "partial_route_count": counts["partial"],
        "planned_route_count": counts["planned"],
        "acquisition_plans_generated": len(acquisition.get("repair_tasks") or []),
        "next_best_actions": list(dict.fromkeys((valuation.get("next_actions") or []) + (demand.get("next_actions") or []) + (acquisition.get("next_actions") or [])))[:8],
    }


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, watchlist: str = "ai_core") -> dict:
    rows = [build_ticker_result(conn, ticker, watchlist=watchlist) for ticker in tickers]
    blockers_checked = sum(row.get("blockers_checked") or 0 for row in rows)
    blockers_without = sum(row.get("blockers_without_routes") or 0 for row in rows)
    summary = {
        "tickers_checked": len(rows),
        "blockers_with_source_routes": blockers_checked - blockers_without,
        "blockers_without_source_routes": blockers_without,
        "implemented_routes": sum(row.get("implemented_route_count") or 0 for row in rows),
        "partial_routes": sum(row.get("partial_route_count") or 0 for row in rows),
        "planned_routes": sum(row.get("planned_route_count") or 0 for row in rows),
        "acquisition_plans_generated": sum(row.get("acquisition_plans_generated") or 0 for row in rows),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if summary["blockers_without_source_routes"] == 0 else "partial_pass",
        "summary": summary,
        "ticker_results": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "planned_route_used_as_evidence": False,
            "new_pending_created": False,
            "paper_order_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 23 source routing")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, parse_tickers(args.tickers, args.watchlist if not args.tickers else None), watchlist=args.watchlist)
        register_snapshot(
            conn,
            entity_type="phase23_source_routing_revalidation",
            entity_id=args.tickers or args.watchlist,
            status=payload["overall_status"],
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase23 source routing revalidation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
