#!/usr/bin/env python3
"""Manual daily-bar backfill wrapper with post-run health recompute."""

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

SCRIPT_NAME = "repair_daily_bar_backfill.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill A/H/US daily bars and recompute health")
    parser.add_argument("--market", choices=["A", "H", "US"], required=True)
    parser.add_argument("--days", type=int, default=45)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    command = [sys.executable, str(project_path("08_scripts", "data_harvester", "ah_daily_bar.py")), "--days", str(args.days)]
    if args.market == "A":
        command.append("--a-only")
    elif args.market == "H":
        command.append("--hk-only")
    else:
        command.append("--us-only")

    if args.dry_run:
        print(" ".join(command))
        log_run(SCRIPT_NAME, "success", "daily-bar repair dry run", {"market": args.market, "command": command})
        return

    subprocess.run(command, check=True)
    subprocess.run([sys.executable, str(project_path("08_scripts", "jobs", "recompute_data_source_health.py"))], check=False)
    log_run(SCRIPT_NAME, "success", "daily-bar repair completed", {"market": args.market, "days": args.days})


if __name__ == "__main__":
    main()
