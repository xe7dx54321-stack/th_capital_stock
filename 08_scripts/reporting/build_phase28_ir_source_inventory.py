#!/usr/bin/env python3
"""Build Phase 28 real-source IR inventory."""

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
from smr_ir_source_inventory import build_ir_source_inventory
from smr_phase25_utils import resolve_phase25_tickers
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, allow_mock_fallback: bool = True) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = [
        build_ir_source_inventory(item, conn=conn, use_real_sources=True, allow_mock_fallback=allow_mock_fallback)
        for item in resolved
    ]
    source_types: dict[str, int] = {}
    ticker_results = []
    for row in rows:
        inv = row.get("source_inventory") or {}
        for key, value in (inv.get("sources_by_type") or {}).items():
            source_types[key] = source_types.get(key, 0) + value
        ticker_results.append(
            {
                "ticker": row.get("ticker"),
                "real_sources_found": inv.get("real_sources_found", 0),
                "source_types": list((inv.get("sources_by_type") or {}).keys()),
                "mock_fallback_used": bool(inv.get("mock_fallback_used")),
            }
        )
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "real_sources_found": sum((row.get("source_inventory") or {}).get("real_sources_found", 0) for row in rows),
            "mock_sources_used": sum((row.get("source_inventory") or {}).get("mock_sources_used", 0) for row in rows),
            "source_missing": sum(1 for row in rows if (row.get("source_inventory") or {}).get("source_missing")),
            "source_types": source_types,
        },
        "ticker_results": ticker_results,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 28 IR source inventory")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--allow-mock-fallback", action="store_true", default=True)
    parser.add_argument("--no-mock-fallback", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, allow_mock_fallback=not args.no_mock_fallback)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
