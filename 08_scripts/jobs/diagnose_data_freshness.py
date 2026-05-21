#!/usr/bin/env python3
"""Print and persist freshness diagnostics for critical SMR data sources."""

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
from smr_data_diagnostics import diagnose_data_freshness
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "diagnose_data_freshness.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose stale/missing data source health")
    parser.add_argument("--no-refresh", action="store_true", help="Use existing health rows without recomputing")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a compact table")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = diagnose_data_freshness(conn, refresh=not args.no_refresh)
        register_snapshot(
            conn,
            entity_type="data_freshness_diagnostic_snapshot",
            entity_id="latest",
            status="success",
            source=SCRIPT_NAME,
            payload={"diagnostics": rows},
        )
        conn.commit()
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for row in rows:
                missing = ",".join(row.get("missing_sessions") or [])
                print(
                    f"{row.get('source_key')}[{row.get('market')}] "
                    f"{row.get('health_status')}/{row.get('blocking_level')} "
                    f"expected={row.get('expected_latest_trading_day') or '-'} "
                    f"actual={row.get('actual_latest_trading_day') or row.get('last_data_timestamp') or '-'} "
                    f"cause={row.get('probable_cause')} "
                    f"missing={missing or '-'}"
                )
        log_run(SCRIPT_NAME, "success", "data freshness diagnostics generated", {"row_count": len(rows)})
    finally:
        conn.close()


if __name__ == "__main__":
    main()
