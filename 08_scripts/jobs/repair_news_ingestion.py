#!/usr/bin/env python3
"""Run the public-news refresh chain and recompute news health."""

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

SCRIPT_NAME = "repair_news_ingestion.py"

PIPELINE = [
    ("08_scripts/wiki/fetch_eastmoney_news_search.py", ["--limit", "80", "--per-symbol-limit", "5"]),
    ("08_scripts/wiki/fetch_eastmoney_news_articles.py", ["--limit", "80", "--article-limit", "3"]),
    ("08_scripts/wiki/build_source_manifest.py", []),
    ("08_scripts/events/normalize_market_events.py", []),
    ("08_scripts/jobs/ingest_news.py", ["--from-manifest", "--export-evidence"]),
    ("08_scripts/jobs/recompute_news_health.py", []),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair news ingestion and recompute health")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    commands = [[sys.executable, str(project_path(*path.split("/"))), *extra] for path, extra in PIPELINE]
    if args.dry_run:
        for command in commands:
            print(" ".join(command))
        log_run(SCRIPT_NAME, "success", "news repair dry run", {"command_count": len(commands)})
        return 0

    failures = []
    for command in commands:
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            failures.append({"command": command, "returncode": result.returncode})
            if not args.continue_on_error:
                break
    log_run(
        SCRIPT_NAME,
        "failed" if failures else "success",
        "news repair completed" if not failures else "news repair had failures",
        {"command_count": len(commands), "failures": failures},
    )
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
