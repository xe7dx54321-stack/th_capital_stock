#!/usr/bin/env python3
"""Build Phase 22 demand-to-valuation linkage diagnostics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_demand_valuation_linkage import build_demand_valuation_linkage, demand_valuation_linkage_improved
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase22_demand_valuation_linkage.py"


def parse_tickers(raw: str | None, watchlist: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if watchlist:
        return [str(item.get("ticker") or "").upper() for item in load_watchlist_config(watchlist).get("tickers") or [] if item.get("ticker")]
    return []


def build_payload(conn: sqlite3.Connection, *, watchlist: str = "ai_core", tickers: str | None = None) -> dict:
    rows = [build_demand_valuation_linkage(conn, ticker, persist=True) for ticker in parse_tickers(tickers, watchlist)]
    if len(rows) == 1 and tickers:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist,
        "summary": {
            "tickers_checked": len(rows),
            "demand_valuation_linkage_improved": sum(1 for row in rows if demand_valuation_linkage_improved(row)),
            "strong_support": sum(1 for row in rows if (row.get("demand_valuation_linkage") or {}).get("status") == "strong_support"),
            "medium_support": sum(1 for row in rows if (row.get("demand_valuation_linkage") or {}).get("status") == "medium_support"),
            "weak_or_missing": sum(1 for row in rows if (row.get("demand_valuation_linkage") or {}).get("status") in {"weak_support", "context_only", "missing", "conflicted"}),
        },
        "ticker_results": rows,
        "safety": {
            "demand_replaces_valuation_model": False,
            "promotion_rules_relaxed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 22 demand-to-valuation linkage")
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
            entity_type="phase22_demand_valuation_linkage",
            entity_id=args.tickers or args.watchlist,
            status="diagnosed",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase22 demand-to-valuation linkage built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
