#!/usr/bin/env python3
"""Build lightweight valuation snapshots for selected tickers."""

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
from smr_data_health import get_system_data_health
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_valuation import build_valuation_snapshot

SCRIPT_NAME = "build_valuation_snapshot.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build valuation snapshots")
    parser.add_argument("--ticker", action="append", help="Ticker to snapshot; repeatable")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    try:
        tickers = args.ticker or [
            row[0]
            for row in conn.execute(
                """
                SELECT DISTINCT ticker
                FROM decision_ledger
                WHERE ticker IS NOT NULL
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (args.limit,),
            ).fetchall()
        ]
        health = get_system_data_health(conn, refresh=False)
        snapshots = [build_valuation_snapshot(conn, ticker, health) for ticker in tickers]
        register_snapshot(
            conn,
            entity_type="valuation_snapshot_batch",
            entity_id="latest",
            status="success",
            source=SCRIPT_NAME,
            payload={"snapshots": snapshots},
        )
        conn.commit()
    finally:
        conn.close()
    log_run(SCRIPT_NAME, "success", "valuation snapshots built", {"ticker_count": len(tickers)})
    print(json.dumps(snapshots, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
