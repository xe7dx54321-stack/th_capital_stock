#!/usr/bin/env python3
"""Link recovered financial statement chunks to evidence graph."""

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

from extract_financial_statement_chunks import extract_for_ticker
from smr_agents import DB_PATH
from smr_financial_statement_chunker import upsert_financial_statement_chunks
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(db_path: str, ticker: str, *, live: bool = True) -> dict:
    ticker = ticker.upper()
    conn = sqlite3.connect(db_path)
    try:
        extraction = extract_for_ticker(conn, ticker, live=live)
        source = (extraction.get("source_recovery") or {}).get("best_source") or extraction.get("source") or {}
        chunks = extraction.get("chunks") or []
        linkage = upsert_financial_statement_chunks(conn, ticker, source, chunks) if source and chunks else {
            "ticker": ticker,
            "source_id": source.get("source_id") if source else None,
            "chunks_linked": 0,
            "evidence_linked": [],
        }
        payload = {
            "generated_at": now_ts(),
            "ticker": ticker,
            "source_id": source.get("source_id") if source else None,
            "source_found": bool(source),
            "chunks_found": len(chunks),
            "evidence_linked_count": len(linkage.get("evidence_linked") or []),
            "evidence_linked": linkage.get("evidence_linked") or [],
            "missing_reason": None if linkage.get("evidence_linked") else extraction.get("missing_reason"),
            "extraction": extraction,
        }
        register_snapshot(
            conn,
            entity_type="phase17_financial_statement_chunk_evidence_linkage",
            entity_id=ticker,
            status="success" if payload["evidence_linked_count"] else "missing",
            source="link_financial_statement_chunks_to_evidence.py",
            payload=payload,
        )
        conn.commit()
        return payload
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Link financial statement chunks to evidence graph")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.db_path, args.ticker, live=not args.no_live)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("link_financial_statement_chunks_to_evidence.py", "success", "financial statement chunk evidence linkage complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
