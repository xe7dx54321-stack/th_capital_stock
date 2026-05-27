#!/usr/bin/env python3
"""Fetch/normalize Phase 28 real IR source metadata."""

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
from smr_phase25_utils import resolve_phase25_tickers
from smr_real_ir_source_connector import build_real_ir_source_payload
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "fetch_real_ir_sources.py"


def build_payload(conn: sqlite3.Connection, *, ticker: str | None = None, tickers: str | None = None, mode: str = "dry_run") -> dict:
    resolved = resolve_phase25_tickers(ticker or tickers)
    rows = [build_real_ir_source_payload(conn, item, mode=mode) for item in resolved]
    payload = {
        "generated_at": now_ts(),
        "mode": mode,
        "summary": {
            "tickers_checked": len(rows),
            "sources_found": sum(row.get("sources_found", 0) for row in rows),
            "sources_written": sum(row.get("sources_written", 0) for row in rows),
            "source_missing": sum(1 for row in rows if row.get("source_missing")),
            "raw_content_saved": False,
        },
        "rows": rows,
    }
    if len(rows) == 1 and ticker and not tickers:
        return {**rows[0], "generated_at": payload["generated_at"]}
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize real IR source metadata")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, tickers=args.tickers, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase28_real_ir_sources", args.ticker or args.tickers or "supply_chain_pilot", mode, SCRIPT_NAME, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase28 real IR sources normalized", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
