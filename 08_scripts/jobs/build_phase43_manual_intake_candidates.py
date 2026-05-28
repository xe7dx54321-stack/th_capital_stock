#!/usr/bin/env python3
"""Build Phase 43 manual intake evidence candidates."""

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
from smr_manual_intake_candidate_generator import build_candidate_generation_payload
from smr_registry import register_snapshot
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "build_phase43_manual_intake_candidates.py"


def build_payload(conn: sqlite3.Connection, *, ticker: str, sample: str | None = None, mode: str = "dry_run") -> dict:
    return build_candidate_generation_payload(conn, ticker=ticker, sample=sample, mode=mode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 43 manual intake candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--sample")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, sample=args.sample, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase43_manual_intake_candidates", args.ticker.upper(), mode, SCRIPT_NAME, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
