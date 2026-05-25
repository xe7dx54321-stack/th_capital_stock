#!/usr/bin/env python3
"""Extract financial statement chunks from discovered sources."""

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
from smr_financial_statement_chunker import extract_financial_statement_chunks_from_source
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


def extract_for_ticker(conn: sqlite3.Connection, ticker: str, *, live: bool = True) -> dict:
    discovery = discover_financial_statement_sources(conn, ticker, live=live)
    best = discovery.get("best_source")
    if not best:
        return {
            "ticker": ticker,
            "source_recovery": discovery,
            "source_id": None,
            "chunks": [],
            "missing_reason": discovery.get("missing_reason") or "financial_statement_source_not_found",
        }
    try:
        result = extract_financial_statement_chunks_from_source(ticker, best)
        result["source_recovery"] = discovery
        return result
    except Exception as exc:
        return {
            "ticker": ticker,
            "source_recovery": discovery,
            "source_id": best.get("source_id"),
            "chunks": [],
            "missing_reason": "source_chunk_extraction_failed",
            "error": str(exc),
            "suggested_fix": "improve PDF table extraction or source selection",
        }


def build_payload(db_path: str, tickers: list[str], *, live: bool = True) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        results = [extract_for_ticker(conn, ticker, live=live) for ticker in tickers]
        payload = {
            "generated_at": now_ts(),
            "tickers": results,
            "summary": {
                "targets": tickers,
                "sources_found": sum(1 for item in results if item.get("source_id")),
                "chunks_found": sum(len(item.get("chunks") or []) for item in results),
                "income_statement_chunks": sum((item.get("section_counts") or {}).get("income_statement", 0) for item in results),
                "balance_sheet_chunks": sum((item.get("section_counts") or {}).get("balance_sheet", 0) for item in results),
            },
        }
        register_snapshot(
            conn,
            entity_type="phase17_financial_statement_chunk_extraction",
            entity_id="latest",
            status="success" if payload["summary"]["chunks_found"] else "missing",
            source="extract_financial_statement_chunks.py",
            payload=payload,
        )
        conn.commit()
        return payload
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract financial statement chunks")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.db_path, parse_tickers(args.tickers, args.ticker), live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("extract_financial_statement_chunks.py", "success", "financial statement chunk extraction complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
