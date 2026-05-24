#!/usr/bin/env python3
"""Phase 11 historical valuation snapshot builder."""

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
from smr_fundamentals import historical_fundamental_support
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import build_historical_valuation, latest_factor, valuation_sub_blockers
from smr_wiki import now_ts


SCRIPT_NAME = "build_historical_valuation_snapshot.py"


def build_historical_valuation_payload(conn: sqlite3.Connection, ticker: str, *, lookback_years: int = 3) -> dict[str, Any]:
    factor = latest_factor(conn, ticker)
    historical = build_historical_valuation(conn, ticker, factor, lookback_years=lookback_years)
    fundamentals_support = historical_fundamental_support(conn, ticker)
    available_metrics = [metric for metric, detail in (historical.get("metrics") or {}).items() if detail.get("status") == "available"]
    missing_metrics = [metric for metric, detail in (historical.get("metrics") or {}).items() if detail.get("status") != "available"]
    blockers = [
        item["code"]
        for item in valuation_sub_blockers(
            {
                "ticker": ticker,
                "historical_valuation": historical,
                "historical_percentile_status": historical.get("status"),
                "historical_percentile": historical.get("primary_percentile"),
                "missing_data": ["historical_percentile"] if historical.get("status") == "missing" else [],
                "valuation_confidence": 0.5,
            }
        )
        if item["code"].startswith("HISTORICAL_")
    ]
    return {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "historical_valuation": historical,
        "historical_fundamentals": fundamentals_support,
        "available_metrics": available_metrics,
        "missing_metrics": missing_metrics,
        "remaining_historical_blockers": sorted(set(blockers)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 11 historical valuation snapshot")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="09988.HK")
    parser.add_argument("--lookback-years", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = build_historical_valuation_payload(conn, args.ticker, lookback_years=args.lookback_years)
        register_snapshot(
            conn,
            entity_type="phase11_historical_valuation",
            entity_id=args.ticker.upper(),
            status=(payload.get("historical_valuation") or {}).get("status") or "unknown",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase11 historical valuation built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
