#!/usr/bin/env python3
"""Route demand/order/tender/proxy blockers to Phase 23 source connectors."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
PHASE22_REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, PHASE22_REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase22_confirmed_demand_evidence import build_ticker_confirmed_demand
from build_phase22_proxy_strengthening import build_ticker_proxy_strengthening
from smr_agents import DB_PATH
from smr_blocker_source_router import build_source_routes_for_blocker
from smr_phase6_watchlists import load_watchlist_config, watchlist_map
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_source_connector_registry import infer_market_from_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase23_demand_source_routing.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def _market_for(ticker: str, watchlist: str) -> str:
    item = watchlist_map(watchlist).get(ticker.upper()) or {}
    return infer_market_from_ticker(ticker, item.get("market"))


def demand_blockers_for_ticker(conn: sqlite3.Connection, ticker: str, *, watchlist: str) -> list[str]:
    confirmed = build_ticker_confirmed_demand(conn, ticker).get("confirmed_demand_evidence") or {}
    proxy = build_ticker_proxy_strengthening(conn, ticker, watchlist=watchlist).get("proxy_strengthening") or {}
    proxy_after = proxy.get("after") or {}
    blockers: list[str] = []
    if (confirmed.get("confirmed_order_count") or 0) == 0:
        blockers.append("CONFIRMED_ORDER_EVIDENCE_MISSING")
    if (confirmed.get("tender_or_procurement_count") or 0) == 0:
        blockers.extend(["TENDER_EVIDENCE_MISSING", "PROCUREMENT_EVIDENCE_MISSING"])
    if (confirmed.get("customer_capex_count") or 0) == 0:
        blockers.append("CUSTOMER_CAPEX_EVIDENCE_MISSING")
    if (confirmed.get("strong_or_medium_indication_count") or 0) == 0:
        blockers.append("DIRECT_DEMAND_EVIDENCE_MISSING")
    if (proxy_after.get("independent_source_count") or 0) < 2:
        blockers.append("PROXY_INDEPENDENT_SOURCE_MISSING")
    for requirement in proxy.get("remaining_requirements") or []:
        text = str(requirement).lower()
        if "dominant_proxy_signal" in text:
            blockers.append("DOMINANT_PROXY_SIGNAL_MISSING")
        elif "stronger direct demand evidence" in text:
            blockers.append("DIRECT_DEMAND_EVIDENCE_MISSING")
        elif "independent_source_count" in text:
            blockers.append("PROXY_INDEPENDENT_SOURCE_MISSING")
    return list(dict.fromkeys(blockers))


def _flatten_routes(bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [route for bundle in bundles for route in bundle.get("source_routes") or []]


def build_ticker_payload(conn: sqlite3.Connection, ticker: str, *, watchlist: str = "ai_core") -> dict[str, Any]:
    market = _market_for(ticker, watchlist)
    blockers = demand_blockers_for_ticker(conn, ticker, watchlist=watchlist)
    bundles = [build_source_routes_for_blocker(blocker, ticker, market) for blocker in blockers]
    routes = _flatten_routes(bundles)
    return {
        "ticker": ticker.upper(),
        "market": market,
        "demand_blockers": blockers,
        "source_routes": routes,
        "source_route_bundles": bundles,
        "next_actions": list(dict.fromkeys(route.get("next_action") for route in routes if route.get("next_action")))[:8],
        "safety": {
            "planned_connector_usable_as_evidence": False,
            "news_treated_as_confirmed_order": False,
            "customer_capex_treated_as_order": False,
        },
    }


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict[str, Any]:
    rows = [build_ticker_payload(conn, ticker, watchlist=watchlist) for ticker in parse_tickers(tickers, watchlist)]
    if len(rows) == 1 and tickers:
        return rows[0]
    routes = [route for row in rows for route in row.get("source_routes") or []]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "demand_blockers_checked": sum(len(row.get("demand_blockers") or []) for row in rows),
            "routes_generated": len(routes),
            "blockers_without_source_routes": sum(1 for route in routes if route.get("route_status") == "UNKNOWN_INFORMATION_ROUTE"),
            "planned_routes": sum(1 for route in routes if route.get("route_status") == "planned_only"),
        },
        "ticker_results": rows,
        "safety": {
            "promotion_rules_relaxed": False,
            "planned_connector_usable_as_evidence": False,
            "news_treated_as_confirmed_order": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 23 demand source routing")
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
            entity_type="phase23_demand_source_routing",
            entity_id=args.tickers or args.watchlist,
            status="routed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase23 demand source routing built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
