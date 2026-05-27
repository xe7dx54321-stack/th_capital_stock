#!/usr/bin/env python3
"""Extract clean text from Phase 28 real IR sources for Phase 29."""

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
from smr_document_text_extractor import extract_document_text
from smr_phase25_utils import resolve_phase25_tickers
from smr_real_ir_source_connector import discover_real_ir_sources
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_text_cache import summarize_text_cache
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "extract_real_ir_document_text.py"


def _status_counts(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        status = result.get("extraction_status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, mode: str = "dry_run") -> dict:
    rows = []
    all_results = []
    for ticker in resolve_phase25_tickers(tickers):
        sources = discover_real_ir_sources(conn, ticker)
        results = [extract_document_text(source, write_cache=(mode == "execute")) for source in sources]
        counts = _status_counts(results)
        all_results.extend(results)
        rows.append(
            {
                "ticker": ticker,
                "sources_checked": len(sources),
                "text_extracted": counts.get("text_extracted", 0),
                "metadata_only": counts.get("metadata_only", 0),
                "text_too_short": counts.get("text_too_short", 0),
                "scanned_pdf_needs_ocr": counts.get("scanned_pdf_needs_ocr", 0),
                "extraction_failed": counts.get("extraction_failed", 0),
                "text_cache_written": sum(1 for item in results if item.get("text_cache_path")),
                "results": [{k: v for k, v in item.items() if k != "text"} for item in results],
            }
        )
    counts = _status_counts(all_results)
    return {
        "generated_at": now_ts(),
        "mode": mode,
        "summary": {
            "tickers_checked": len(rows),
            "sources_checked": len(all_results),
            "text_extracted": counts.get("text_extracted", 0),
            "metadata_only": counts.get("metadata_only", 0),
            "text_too_short": counts.get("text_too_short", 0),
            "scanned_pdf_needs_ocr": counts.get("scanned_pdf_needs_ocr", 0),
            "table_only": counts.get("table_only", 0),
            "download_unavailable": counts.get("download_unavailable", 0),
            "extraction_failed": counts.get("extraction_failed", 0),
            "raw_files_committed": 0,
            "text_cache_written": sum(row.get("text_cache_written", 0) for row in rows),
            "text_cache": summarize_text_cache(),
        },
        "ticker_results": rows,
        "safety": {
            "dry_run_wrote_cache": False if mode == "dry_run" else None,
            "raw_pdf_html_saved": False,
            "ocr_default_enabled": False,
            "metadata_used_as_body": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract real IR document text")
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
        payload = build_payload(conn, tickers=args.ticker or args.tickers, mode=mode)
        if mode == "execute":
            register_snapshot(conn, "phase29_document_text_extraction", args.ticker or args.tickers or "supply_chain_pilot", mode, SCRIPT_NAME, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase29 real IR document text extracted", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
