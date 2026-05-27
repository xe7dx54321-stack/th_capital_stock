#!/usr/bin/env python3
"""Build Phase 28 real IR semantic evidence summary."""

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
from smr_phase25_utils import resolve_phase25_tickers
from smr_phase27_semantic_pipeline import build_semantic_pipeline_for_ticker
from smr_semantic_evidence_persistence import candidates_from_pipeline
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None) -> dict:
    resolved = resolve_phase25_tickers(tickers)
    rows = []
    by_variable: dict[str, int] = {}
    for ticker in resolved:
        pipeline = build_semantic_pipeline_for_ticker(ticker, conn=conn, use_real_sources=True, allow_mock_fallback=True)
        candidates = candidates_from_pipeline(pipeline)
        passed = [gate for gate in pipeline.get("gate_results") or [] if gate.get("evidence_status") != "blocked"]
        variables = list(dict.fromkeys(str(gate.get("variable_type")) for gate in passed if gate.get("variable_type")))
        for variable in variables:
            by_variable[variable] = by_variable.get(variable, 0) + 1
        rows.append(
            {
                "ticker": ticker,
                "real_sources_found": pipeline.get("real_sources_used"),
                "mock_sources_used": pipeline.get("mock_sources_used"),
                "chunks_processed": len(pipeline.get("chunks") or []),
                "semantic_extractions": len(pipeline.get("semantic_extractions") or []),
                "passed_gate": len(passed),
                "evidence_candidates": len(candidates),
                "main_variables": variables[:6],
                "limitations": ["no supplier share", "no ASP", "no customer allocation", "no official consensus"],
            }
        )
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "real_sources_found": sum(row.get("real_sources_found", 0) for row in rows),
            "mock_sources_used": sum(row.get("mock_sources_used", 0) for row in rows),
            "chunks_processed": sum(row.get("chunks_processed", 0) for row in rows),
            "semantic_extractions": sum(row.get("semantic_extractions", 0) for row in rows),
            "passed_gate": sum(row.get("passed_gate", 0) for row in rows),
            "evidence_candidates_created": sum(row.get("evidence_candidates", 0) for row in rows),
            "variable_packs_updated": sum(1 for row in rows if row.get("evidence_candidates")),
            "new_pending_created": 0,
        },
        "by_variable_type": by_variable,
        "rows": rows,
        "safety": {
            "semantic_evidence_alone_pending": False,
            "promotion_rules_relaxed": False,
            "raw_large_files_written": False,
        },
    }


def render_markdown(payload: dict) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 28 Real IR Semantic Evidence Summary",
        "",
        "## Overall",
        f"- Real sources found: {summary.get('real_sources_found')}",
        f"- Mock sources used: {summary.get('mock_sources_used')}",
        f"- Chunks processed: {summary.get('chunks_processed')}",
        f"- Semantic extractions: {summary.get('semantic_extractions')}",
        f"- Passed gate: {summary.get('passed_gate')}",
        f"- Evidence candidates: {summary.get('evidence_candidates_created')}",
        f"- Variable packs updated: {summary.get('variable_packs_updated')}",
        f"- New pending: {summary.get('new_pending_created')}",
        "",
        "## By Variable",
        "| Variable | Count |",
        "|---|---|",
    ]
    for variable, count in sorted((payload.get("by_variable_type") or {}).items()):
        lines.append(f"| {variable} | {count} |")
    lines.extend(["", "## By Ticker", "| Ticker | Real Sources | Extractions | Candidates | Main Variables | Limitations |", "|---|---|---|---|---|---|"])
    for row in payload.get("rows") or []:
        lines.append(
            f"| {row.get('ticker')} | {row.get('real_sources_found')} | {row.get('semantic_extractions')} | "
            f"{row.get('evidence_candidates')} | {', '.join(row.get('main_variables') or [])} | {'; '.join(row.get('limitations') or [])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 28 real IR semantic summary")
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
