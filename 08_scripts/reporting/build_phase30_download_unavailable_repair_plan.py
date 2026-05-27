#!/usr/bin/env python3
"""Build Phase 30 repair plan for download-unavailable real IR sources."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(JOBS_DIR) not in sys.path:
    sys.path.insert(0, str(JOBS_DIR))

from extract_real_ir_document_text import build_payload as build_extraction_payload
from smr_agents import DB_PATH
from smr_phase25_utils import resolve_phase25_tickers
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _repair_action(result: dict) -> str:
    status = result.get("extraction_status")
    reason = str(result.get("reason") or "").lower()
    if status == "scanned_pdf_needs_ocr":
        return "needs_ocr_optional"
    if status == "download_unavailable" and "local file path" in reason:
        return "manual_text_needed"
    if status == "download_unavailable":
        return "retry_with_headers_or_alt_url"
    if status == "text_too_short":
        return "alternate_source_needed"
    return "mark_unavailable"


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    sources = []
    for ticker in resolve_phase25_tickers(tickers):
        extraction = build_extraction_payload(conn, tickers=ticker, mode="dry_run")
        for ticker_result in extraction.get("ticker_results") or []:
            for result in ticker_result.get("results") or []:
                if result.get("extraction_status") == "text_extracted":
                    continue
                action = _repair_action(result)
                sources.append(
                    {
                        "source_id": result.get("source_id"),
                        "ticker": ticker,
                        "source_url": result.get("source_url"),
                        "failure_reason": result.get("extraction_status"),
                        "detail": result.get("reason") or "; ".join(result.get("limitations") or []),
                        "repair_action": action,
                        "priority": "medium" if action in {"retry_with_headers_or_alt_url", "manual_text_needed"} else "low",
                    }
                )
    actions = Counter(source.get("repair_action") for source in sources)
    return {
        "generated_at": now_ts(),
        "summary": {
            "download_unavailable_sources": sum(1 for source in sources if source.get("failure_reason") == "download_unavailable"),
            "retry_candidates": actions.get("retry_with_headers_or_alt_url", 0),
            "manual_text_needed": actions.get("manual_text_needed", 0),
            "alternate_source_needed": actions.get("alternate_source_needed", 0),
        },
        "sources": sources,
        "safety": {
            "auto_download_bypass": False,
            "ocr_default_enabled": False,
            "body_text_fabricated": False,
            "evidence_written": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 30 download unavailable repair plan")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
