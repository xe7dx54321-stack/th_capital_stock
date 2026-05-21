#!/usr/bin/env python3
"""Build ticker-level fundamentals snapshots."""

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
from smr_fundamentals import build_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "build_fundamentals_snapshot.py"


def parse_tickers(raw: str | None) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build fundamentals_snapshot rows")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--no-live", action="store_true", help="Skip live SEC companyfacts fetch and use local factors/filings only")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        results = [
            build_fundamentals_snapshot(conn, ticker, timeout=args.timeout, prefer_live=not args.no_live)
            for ticker in parse_tickers(args.tickers)
        ]
        status = "updated" if any(item.get("freshness_status") in {"fresh", "degraded"} for item in results) else "empty"
        register_snapshot(
            conn,
            entity_type="fundamentals_snapshot_batch",
            entity_id="latest",
            status=status,
            source=SCRIPT_NAME,
            payload={"results": results},
        )
        conn.commit()
    finally:
        conn.close()
    payload = {"status": status, "results": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "fundamentals snapshots built", {"status": status, "count": len(results)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
