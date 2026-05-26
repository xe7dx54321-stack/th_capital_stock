#!/usr/bin/env python3
"""Route Phase 22 valuation blockers to Phase 23 source connectors."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_blocker_source_router import build_source_routes_for_blocker
from smr_phase6_watchlists import load_watchlist_config, watchlist_map
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_source_connector_registry import infer_market_from_ticker
from smr_valuation_gate_v2 import diagnose_valuation_gate_v2
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase23_valuation_source_routing.py"


def parse_tickers(raw: str | None, ticker: str | None = None, watchlist: str | None = None) -> list[str]:
    if ticker:
        return [ticker.strip().upper()]
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _market_for(ticker: str, watchlist: str) -> str:
    item = watchlist_map(watchlist).get(ticker.upper()) or {}
    return infer_market_from_ticker(ticker, item.get("market"))


def _flatten_routes(bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [route for bundle in bundles for route in bundle.get("source_routes") or []]


def build_ticker_payload(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict[str, Any]:
    market = _market_for(ticker, watchlist)
    valuation = diagnose_valuation_gate_v2(conn, ticker, watchlist_id=watchlist)
    gate = valuation.get("valuation_gate_v2") or {}
    blockers = list(gate.get("remaining_blockers") or [])
    bundles = [build_source_routes_for_blocker(blocker, ticker, market) for blocker in blockers]
    routes = _flatten_routes(bundles)
    return {
        "ticker": ticker.upper(),
        "market": market,
        "valuation_blockers": blockers,
        "valuation_status": gate.get("after_status"),
        "source_routes": routes,
        "source_route_bundles": bundles,
        "next_actions": list(dict.fromkeys(route.get("next_action") for route in routes if route.get("next_action")))[:8],
        "safety": {
            "official_consensus_implemented": False,
            "internal_proxy_promoted_to_official_consensus": False,
            "planned_connector_usable_as_evidence": False,
        },
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    routes = [route for row in rows for route in row.get("source_routes") or []]
    return {
        "tickers_checked": len(rows),
        "valuation_blockers_checked": sum(len(row.get("valuation_blockers") or []) for row in rows),
        "routes_generated": len(routes),
        "blockers_without_source_routes": sum(1 for route in routes if route.get("route_status") == "UNKNOWN_INFORMATION_ROUTE"),
        "implemented_routes": sum(1 for route in routes if route.get("route_status") == "implemented"),
        "partial_routes": sum(1 for route in routes if route.get("route_status") == "partial"),
        "planned_routes": sum(1 for route in routes if route.get("route_status") == "planned_only"),
    }


def build_payload(
    conn: sqlite3.Connection,
    *,
    watchlist: str = "ai_core",
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    rows = [build_ticker_payload(conn, item, watchlist=watchlist) for item in parse_tickers(tickers, ticker, watchlist if not ticker and not tickers else None)]
    if len(rows) == 1 and ticker:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": _summary(rows),
        "ticker_results": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "official_consensus_implemented": False,
            "planned_connector_usable_as_evidence": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 23 valuation source routing")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, watchlist=args.watchlist, ticker=args.ticker, tickers=args.tickers)
        register_snapshot(
            conn,
            entity_type="phase23_valuation_source_routing",
            entity_id=args.ticker or args.tickers or args.watchlist,
            status="routed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase23 valuation source routing built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
