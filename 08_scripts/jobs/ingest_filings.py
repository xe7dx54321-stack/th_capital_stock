#!/usr/bin/env python3
"""Ingest official filings/announcements and export chunks to evidence."""

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
from smr_filings_ingestion import (
    export_filings_to_evidence,
    ingest_filings_from_manifest,
    seed_filing_document,
    update_filings_health_rows,
)
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "ingest_filings.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest SMR filing documents")
    parser.add_argument("--from-manifest", action="store_true", help="Ingest filings from source_manifest")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--market", help="Accepted for CLI symmetry; manifest ingestion infers market per row")
    parser.add_argument("--watchlist-only", action="store_true", help="Reserved for future upstream fetch filtering")
    parser.add_argument("--seed-ticker")
    parser.add_argument("--seed-title")
    parser.add_argument("--seed-body", default="")
    parser.add_argument("--seed-source-key", default="manual_filing")
    parser.add_argument("--seed-published-at")
    parser.add_argument("--seed-market")
    parser.add_argument("--seed-filing-type")
    parser.add_argument("--export-evidence", action="store_true")
    parser.add_argument("--skip-health", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        metrics = {"manifest": {}, "seed": None, "evidence": {}, "health": {}}
        if args.seed_title:
            if not args.seed_ticker:
                raise SystemExit("--seed-ticker is required when --seed-title is provided")
            metrics["seed"] = seed_filing_document(
                conn,
                ticker=args.seed_ticker,
                title=args.seed_title,
                body=args.seed_body,
                source_key=args.seed_source_key,
                published_at=args.seed_published_at,
                market=args.seed_market or args.market,
                filing_type=args.seed_filing_type,
            )
        if args.from_manifest or not args.seed_title:
            metrics["manifest"] = ingest_filings_from_manifest(conn, limit=args.limit)
        if args.export_evidence:
            metrics["evidence"] = export_filings_to_evidence(conn, limit=args.limit)
        if not args.skip_health:
            metrics["health"] = update_filings_health_rows(conn)
        register_snapshot(
            conn,
            entity_type="filings_ingestion_snapshot",
            entity_id="latest",
            status="updated",
            source=SCRIPT_NAME,
            payload={**metrics, "watchlist_only": args.watchlist_only, "market": args.market},
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(metrics, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "filings ingested", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
