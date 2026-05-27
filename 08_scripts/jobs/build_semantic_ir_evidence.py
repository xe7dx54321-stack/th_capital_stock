#!/usr/bin/env python3
"""Build Phase 27 semantic IR evidence."""

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
from smr_phase27_semantic_pipeline import build_semantic_pipeline
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(
    *,
    tickers: str | None = None,
    mode: str = "mock",
    conn: sqlite3.Connection | None = None,
    use_real_sources: bool = False,
    allow_mock_fallback: bool = True,
    use_text_cache: bool = False,
    extract_text_if_missing: bool = False,
    skip_metadata_only: bool = True,
) -> dict:
    pipeline = build_semantic_pipeline(
        tickers,
        mode=mode,
        conn=conn,
        use_real_sources=use_real_sources,
        allow_mock_fallback=allow_mock_fallback,
        use_text_cache=use_text_cache,
        extract_text_if_missing=extract_text_if_missing,
        skip_metadata_only=skip_metadata_only,
    )
    summary = dict(pipeline.get("summary") or {})
    summary["invalid_extractions"] = 0
    ticker_results = [
        {
            "ticker": row.get("ticker"),
            "real_sources_used": row.get("real_sources_used"),
            "mock_sources_used": row.get("mock_sources_used"),
            "chunks_processed": len(row.get("chunks") or []),
            "semantic_extractions": row.get("semantic_extractions"),
            "no_extraction_chunks": row.get("no_extraction_chunks"),
            "prompt_guardrails": row.get("prompt_guardrails"),
            "llm_enabled": row.get("llm_enabled"),
            "main_variables": list(dict.fromkeys(item.get("variable_type") for item in row.get("semantic_extractions") or [] if item.get("variable_type")))[:6],
            "text_cache_hits": row.get("text_cache_hits"),
            "document_text_extractions": row.get("document_text_extractions"),
            "metadata_only_skipped": row.get("metadata_only_skipped"),
            "quoted_span_validated": row.get("quoted_span_validated"),
            "source_url_preserved": row.get("source_url_preserved"),
        }
        for row in pipeline.get("rows") or []
    ]
    return {
        "generated_at": now_ts(),
        "mode": mode,
        "summary": summary,
        "ticker_results": ticker_results,
        "rows": ticker_results,
        "safety": {
            "llm_default_enabled": False,
            "external_knowledge_allowed": False,
            "customer_names_fabricated": False,
            "confirmed_order_fabricated": False,
            "mock_fallback_explicit": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build semantic IR evidence")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--tickers")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--real-sources", action="store_true")
    parser.add_argument("--allow-mock-fallback", action="store_true", default=True)
    parser.add_argument("--no-mock-fallback", action="store_true")
    parser.add_argument("--use-text-cache", action="store_true")
    parser.add_argument("--extract-text-if-missing", action="store_true")
    parser.add_argument("--skip-metadata-only", action="store_true", default=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "llm" if args.llm and not args.mock else "mock"
    conn = sqlite3.connect(args.db_path) if args.real_sources else None
    try:
        payload = build_payload(
            tickers=args.ticker or args.tickers,
            mode=mode,
            conn=conn,
            use_real_sources=args.real_sources,
            allow_mock_fallback=not args.no_mock_fallback,
            use_text_cache=args.use_text_cache,
            extract_text_if_missing=args.extract_text_if_missing,
            skip_metadata_only=args.skip_metadata_only,
        )
    finally:
        if conn is not None:
            conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
