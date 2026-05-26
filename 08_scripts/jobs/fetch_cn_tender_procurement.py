#!/usr/bin/env python3
"""Run the Phase 24 CN tender/procurement connector."""

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
from smr_cn_tender_procurement import build_cn_tender_procurement_payload
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "fetch_cn_tender_procurement.py"


def parse_tickers(raw: str | None, ticker: str | None = None) -> list[str]:
    if ticker:
        return [ticker.strip().upper()]
    if raw:
        return [item.strip().upper() for item in raw.split(",") if item.strip()]
    return []


def build_payload(conn: sqlite3.Connection, tickers: list[str], *, execute: bool = False) -> dict:
    rows = [build_cn_tender_procurement_payload(conn, ticker, execute=execute) for ticker in tickers]
    if len(rows) == 1:
        return rows[0]
    return {
        "generated_at": now_ts(),
        "connector_id": "cn_tender_procurement",
        "mode": "execute" if execute else "dry_run",
        "summary": {
            "tickers_checked": len(rows),
            "queries_generated": sum(row.get("queries_generated") or 0 for row in rows),
            "raw_results_found": sum(row.get("raw_results_found") or 0 for row in rows),
            "normalized_items": sum(row.get("normalized_items") or 0 for row in rows),
            "evidence_candidates": sum(len(row.get("evidence_candidates") or []) for row in rows),
            "evidence_candidates_written": sum(row.get("evidence_candidates_written") or 0 for row in rows),
            "connector_status": "partial",
        },
        "ticker_results": rows,
        "safety": {
            "raw_files_persisted": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
            "dry_run_writes_evidence_graph": False if not execute else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch/normalize CN tender procurement evidence candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    tickers = parse_tickers(args.tickers, args.ticker)
    if not tickers:
        raise SystemExit("--ticker or --tickers is required")
    execute = bool(args.execute and not args.dry_run)
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers, execute=execute)
        register_snapshot(
            conn,
            entity_type="phase24_cn_tender_procurement_connector",
            entity_id=args.ticker or args.tickers,
            status="executed" if execute else "dry_run",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase24 CN tender procurement connector complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
