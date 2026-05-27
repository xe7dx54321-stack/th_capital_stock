#!/usr/bin/env python3
"""Build Phase 28 real IR source summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fetch_real_ir_sources import build_payload
from smr_agents import DB_PATH

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 28 real IR source summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, mode="dry_run")
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
