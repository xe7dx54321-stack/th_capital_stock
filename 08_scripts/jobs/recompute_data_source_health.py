#!/usr/bin/env python3
"""Recompute data_source_health and the daily system health report."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_data_health import refresh_system_data_health
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "recompute_data_source_health.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute SMR data health")
    parser.add_argument("--skip-report", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        snapshot = refresh_system_data_health(conn)
        register_snapshot(
            conn,
            entity_type="data_freshness_snapshot",
            entity_id="latest",
            status=snapshot.get("overall_status") or "unknown",
            source=SCRIPT_NAME,
            payload=snapshot,
        )
        conn.commit()
    finally:
        conn.close()

    if not args.skip_report:
        subprocess.run(
            [sys.executable, str(project_path("08_scripts", "reporting", "build_daily_system_health_report.py")), "--allow-empty"],
            check=False,
        )
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    log_run(SCRIPT_NAME, "success", "data health recomputed", {"overall_status": snapshot.get("overall_status")})


if __name__ == "__main__":
    main()
