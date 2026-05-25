#!/usr/bin/env python3
"""Discover financial statement sources for Phase 17."""

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
from smr_financial_statement_source_discovery import discover_financial_statement_sources
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_tickers(raw: str | None, ticker: str | None = None) -> list[str]:
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    if ticker:
        return [ticker.strip().upper()]
    return ["00700.HK", "300308.SZ", "688041.SH"]


def build_payload(db_path: str, tickers: list[str], *, live: bool = True) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        results = [discover_financial_statement_sources(conn, ticker, live=live) for ticker in tickers]
        payload = {
            "generated_at": now_ts(),
            "tickers": results,
            "summary": {
                "targets": tickers,
                "sources_found": sum(len(item.get("sources_found") or []) for item in results),
                "best_sources_found": sum(1 for item in results if item.get("best_source")),
                "missing": [item["ticker"] for item in results if not item.get("best_source")],
            },
        }
        register_snapshot(
            conn,
            entity_type="phase17_financial_statement_source_discovery",
            entity_id="latest",
            status="success" if payload["summary"]["best_sources_found"] else "missing",
            source="discover_financial_statement_sources.py",
            payload=payload,
        )
        conn.commit()
        return payload
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover financial statement sources")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.db_path, parse_tickers(args.tickers, args.ticker), live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("discover_financial_statement_sources.py", "success", "financial statement source discovery complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
