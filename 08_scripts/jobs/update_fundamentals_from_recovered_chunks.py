#!/usr/bin/env python3
"""Update fundamentals snapshots from recovered financial statement chunks."""

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

from link_financial_statement_chunks_to_evidence import build_payload as link_payload
from smr_agents import DB_PATH
from smr_recovered_fundamentals import update_fundamentals_from_recovered_chunks
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
    results = []
    for ticker in tickers:
        linkage = link_payload(db_path, ticker, live=live)
        conn = sqlite3.connect(db_path)
        try:
            update = update_fundamentals_from_recovered_chunks(conn, ticker)
            update["source_linkage"] = {
                "source_found": linkage.get("source_found"),
                "chunks_found": linkage.get("chunks_found"),
                "evidence_linked_count": linkage.get("evidence_linked_count"),
                "missing_reason": linkage.get("missing_reason"),
            }
            results.append(update)
            conn.commit()
        finally:
            conn.close()
    payload = {
        "generated_at": now_ts(),
        "results": results,
        "summary": {
            "tickers": tickers,
            "snapshots_updated": sum(1 for item in results if (item.get("fundamentals_snapshot_update") or {}).get("status") == "updated"),
            "fields_updated": sum(len((item.get("fundamentals_snapshot_update") or {}).get("fields_updated") or []) for item in results),
            "fields_skipped": sum(len((item.get("fundamentals_snapshot_update") or {}).get("fields_skipped") or []) for item in results),
        },
    }
    conn = sqlite3.connect(db_path)
    try:
        register_snapshot(
            conn,
            entity_type="phase18_fundamentals_recovered_chunk_update",
            entity_id="latest",
            status="updated" if payload["summary"]["fields_updated"] else "no_recovered_fields",
            source="update_fundamentals_from_recovered_chunks.py",
            payload=payload,
        )
        conn.commit()
        return payload
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Update fundamentals from recovered financial statement chunks")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.db_path, parse_tickers(args.tickers, args.ticker), live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("update_fundamentals_from_recovered_chunks.py", "success", "fundamentals recovered chunk update complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
