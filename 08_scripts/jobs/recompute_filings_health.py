#!/usr/bin/env python3
"""Recompute filings freshness at source, market, watchlist, and ticker scope."""

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
from smr_filings_ingestion import update_filings_health_rows
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "recompute_filings_health.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute SMR filings freshness")
    parser.add_argument("--stale-after-minutes", type=int, default=1440)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        snapshot = update_filings_health_rows(conn, stale_after_minutes=args.stale_after_minutes)
        register_snapshot(
            conn,
            entity_type="filings_freshness_snapshot",
            entity_id="latest",
            status=snapshot.get("overall_status") or "unknown",
            source=SCRIPT_NAME,
            payload=snapshot,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(snapshot, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "filings health recomputed", {"overall_status": snapshot.get("overall_status")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
