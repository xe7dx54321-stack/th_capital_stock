#!/usr/bin/env python3
"""Manual filings/official-materials ingestion wrapper with health recompute."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_runlog import log_run

SCRIPT_NAME = "repair_filings_ingestion.py"

PIPELINE = [
    ("08_scripts/data_harvester/fetch_cninfo_announcements.py", ["--limit", "80"]),
    ("08_scripts/data_harvester/fetch_hkex_announcements.py", ["--limit", "80"]),
    ("08_scripts/data_harvester/fetch_sec_official_materials.py", ["--limit", "40"]),
    ("08_scripts/data_harvester/fetch_ir_primary_materials.py", ["--limit", "40"]),
    ("08_scripts/events/normalize_market_events.py", []),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair filings ingestion and recompute health")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    commands = [[sys.executable, str(project_path(*path.split("/"))), *extra] for path, extra in PIPELINE]
    if args.dry_run:
        for command in commands:
            print(" ".join(command))
        log_run(SCRIPT_NAME, "success", "filings repair dry run", {"command_count": len(commands)})
        return

    failures = []
    for command in commands:
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            failures.append({"command": command, "returncode": result.returncode})
            if not args.continue_on_error:
                break
    subprocess.run([sys.executable, str(project_path("08_scripts", "jobs", "recompute_data_source_health.py"))], check=False)
    if failures:
        log_run(SCRIPT_NAME, "failed", "filings repair had failures", {"failures": failures})
        raise SystemExit(1)
    log_run(SCRIPT_NAME, "success", "filings repair completed", {"command_count": len(commands)})


if __name__ == "__main__":
    main()
