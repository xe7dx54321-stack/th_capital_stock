#!/usr/bin/env python3
"""Validate Phase 34 expectation gap after evidence governance."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_post_governance_evidence_state import build_expectation_gap_post_governance

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None) -> dict[str, Any]:
    return build_expectation_gap_post_governance(conn, ticker=ticker, tickers=tickers)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 34 expectation gap post-governance state")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    summary = payload.get("summary") or {}
    return 0 if summary.get("confidence_upgraded", 0) == 0 and summary.get("new_pending_created", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
