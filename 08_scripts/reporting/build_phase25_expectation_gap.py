#!/usr/bin/env python3
"""Build Phase 25 expectation-gap scoring report."""

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
from smr_expectation_gap import build_expectation_gap
from smr_phase25_utils import resolve_phase25_tickers
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase25_expectation_gap.py"


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None, watchlist: str | None = None) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(ticker or tickers, watchlist)
    rows = [build_expectation_gap(conn, item) for item in resolved]
    positive = {"strong_positive_gap", "potential_positive_gap"}
    payload = {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "positive_gap_candidates": sum(1 for row in rows if (row.get("expectation_gap") or {}).get("status") in positive),
            "insufficient_data": sum(1 for row in rows if (row.get("expectation_gap") or {}).get("status") == "insufficient_data"),
            "conflicted": sum(1 for row in rows if (row.get("expectation_gap") or {}).get("status") == "conflicted"),
            "promotion_allowed": sum(1 for row in rows if (row.get("expectation_gap") or {}).get("promotion_allowed")),
        },
        "rows": rows,
        "safety": {
            "expectation_gap_auto_pending": False,
            "proxy_estimate_treated_as_confirmed": False,
            "official_consensus_treated_as_available": False,
        },
    }
    if len(rows) == 1 and ticker and not tickers:
        return {**rows[0], "generated_at": payload["generated_at"]}
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 25 expectation-gap report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--watchlist")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers, watchlist=args.watchlist)
        register_snapshot(conn, "phase25_expectation_gap", args.ticker or args.tickers or args.watchlist or "supply_chain_pilot", "built", SCRIPT_NAME, payload=payload)
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase25 expectation gap built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
