#!/usr/bin/env python3
"""Build Phase 29 real IR document text extraction summary."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
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
from smr_phase27_semantic_pipeline import build_semantic_pipeline_for_ticker
from smr_semantic_evidence_persistence import candidates_from_pipeline
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = []
    failures = []
    for ticker in resolved:
        extraction = build_extraction_payload(conn, tickers=ticker, mode="dry_run")
        pipeline = build_semantic_pipeline_for_ticker(ticker, conn=conn, use_real_sources=True, use_text_cache=True, allow_mock_fallback=True)
        candidates = candidates_from_pipeline(pipeline)
        summary = extraction.get("summary") or {}
        row = {
            "ticker": ticker,
            "sources_checked": summary.get("sources_checked", 0),
            "text_extracted": summary.get("text_extracted", 0),
            "metadata_only": summary.get("metadata_only", 0),
            "text_too_short": summary.get("text_too_short", 0),
            "scanned_pdf_needs_ocr": summary.get("scanned_pdf_needs_ocr", 0),
            "extraction_failed": summary.get("extraction_failed", 0),
            "chunks_created": len(pipeline.get("chunks") or []),
            "main_sections": list(
                dict.fromkeys((chunk.get("metadata") or {}).get("section_type") for chunk in pipeline.get("chunks") or [] if (chunk.get("metadata") or {}).get("section_type"))
            )[:6],
            "semantic_extractions": len(pipeline.get("semantic_extractions") or []),
            "evidence_candidates": len(candidates),
            "limitations": ["some PDFs metadata-only", "no OCR default"] if summary.get("metadata_only") or summary.get("scanned_pdf_needs_ocr") else [],
        }
        rows.append(row)
        for ticker_result in extraction.get("ticker_results") or []:
            for result in ticker_result.get("results") or []:
                if result.get("extraction_status") != "text_extracted":
                    failures.append(
                        {
                            "source": result.get("source_id"),
                            "ticker": ticker,
                            "status": result.get("extraction_status"),
                            "reason": result.get("reason") or "; ".join(result.get("limitations") or []),
                            "next_fix": "enable OCR or improve PDF text extraction" if result.get("extraction_status") == "scanned_pdf_needs_ocr" else "review source text availability",
                        }
                    )
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "sources_checked": sum(row.get("sources_checked", 0) for row in rows),
            "text_extracted": sum(row.get("text_extracted", 0) for row in rows),
            "metadata_only": sum(row.get("metadata_only", 0) for row in rows),
            "text_too_short": sum(row.get("text_too_short", 0) for row in rows),
            "scanned_pdf_needs_ocr": sum(row.get("scanned_pdf_needs_ocr", 0) for row in rows),
            "extraction_failed": sum(row.get("extraction_failed", 0) for row in rows),
            "chunks_created": sum(row.get("chunks_created", 0) for row in rows),
            "semantic_extractions": sum(row.get("semantic_extractions", 0) for row in rows),
            "evidence_candidates_created": sum(row.get("evidence_candidates", 0) for row in rows),
            "new_pending_created": 0,
        },
        "rows": rows,
        "extraction_failures": failures,
        "safety": {
            "raw_pdf_html_committed": False,
            "ocr_default_enabled": False,
            "semantic_evidence_alone_pending": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 29 Real IR Document Text Extraction Summary",
        "",
        "## Overall",
        f"- Sources checked: {summary.get('sources_checked')}",
        f"- Text extracted: {summary.get('text_extracted')}",
        f"- Metadata only: {summary.get('metadata_only')}",
        f"- Scanned PDFs needing OCR: {summary.get('scanned_pdf_needs_ocr')}",
        f"- Chunks created: {summary.get('chunks_created')}",
        f"- Semantic extractions: {summary.get('semantic_extractions')}",
        f"- Evidence candidates: {summary.get('evidence_candidates_created')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## By Ticker",
        "| Ticker | Sources | Text Extracted | Chunks | Extractions | Candidates | Limitations |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('sources_checked')} | {row.get('text_extracted')} | {row.get('chunks_created')} | "
            f"{row.get('semantic_extractions')} | {row.get('evidence_candidates')} | {'; '.join(row.get('limitations') or [])} |"
        )
    lines.extend(["", "## Extraction Failures", "| Source | Reason | Next Fix |", "|---|---|---|"])
    for item in payload.get("extraction_failures") or []:
        lines.append(f"| {item.get('source')} | {item.get('status')}: {item.get('reason')} | {item.get('next_fix')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 29 text extraction summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
