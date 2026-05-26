#!/usr/bin/env python3
"""Build Phase 25 revenue sensitivity scenarios."""

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
from smr_phase25_utils import resolve_phase25_tickers
from smr_registry import register_snapshot
from smr_revenue_sensitivity_model import build_revenue_sensitivity
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase25_revenue_sensitivity.py"


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None, watchlist: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(ticker or tickers, watchlist)
    rows = [build_revenue_sensitivity(conn, item) for item in resolved]
    payload = {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "scenario_analysis_only": sum(1 for row in rows if (row.get("revenue_sensitivity") or {}).get("allowed_usage") == "scenario_analysis_only"),
            "valuation_supporting": sum(1 for row in rows if (row.get("revenue_sensitivity") or {}).get("valuation_support") == "supporting"),
            "forced_precise_calculations": 0,
        },
        "rows": rows,
        "safety": {
            "supplier_share_fabricated": False,
            "ASP_fabricated": False,
            "customer_allocation_fabricated": False,
        },
    }
    if len(rows) == 1 and ticker and not tickers:
        return {**rows[0], "generated_at": payload["generated_at"]}
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 25 revenue sensitivity")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--watchlist")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers, watchlist=args.watchlist)
        register_snapshot(conn, "phase25_revenue_sensitivity", args.ticker or args.tickers or args.watchlist or "supply_chain_pilot", "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase25 revenue sensitivity built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
