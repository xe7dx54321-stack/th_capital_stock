#!/usr/bin/env python3
"""Build Phase 17 financial statement source chunk recovery summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase17_source_chunk_recovery import build_payload
from smr_agents import DB_PATH
from smr_registry import register_snapshot
from smr_runlog import log_run

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def compact_summary(payload: dict) -> dict:
    ticker_results = []
    for item in payload.get("targets") or []:
        after = item.get("after") or {}
        source = item.get("source_recovery") or {}
        ticker_results.append(
            {
                "ticker": item.get("ticker"),
                "source_found": source.get("financial_statement_source_found"),
                "balance_sheet_chunk_found": source.get("balance_sheet_chunk_found"),
                "income_statement_chunk_found": source.get("income_statement_chunk_found"),
                "evidence_linked": source.get("evidence_linked"),
                "shareholders_equity_status": (after.get("shareholders_equity") or {}).get("status"),
                "revenue_status": (after.get("revenue") or {}).get("status"),
                "gross_profit_status": (after.get("gross_profit") or {}).get("status"),
                "remaining_blockers": item.get("blockers_remaining") or [],
                "source_id": source.get("source_id"),
            }
        )
    return {
        "generated_at": payload.get("generated_at"),
        "summary": payload.get("summary") or {},
        "ticker_results": ticker_results,
    }


def to_markdown(summary: dict) -> str:
    overall = summary.get("summary") or {}
    lines = [
        "# Phase 17 Financial Statement Source Chunk Recovery Summary",
        "",
        "## Overall",
        f"- Sources found: {overall.get('sources_found')}",
        f"- Chunks found: {overall.get('chunks_found')}",
        f"- Evidence linked: {overall.get('evidence_linked')}",
        f"- Fields extracted: {overall.get('fields_extracted')}",
        f"- Fields derived: {overall.get('fields_derived')}",
        f"- Remaining table_not_found: {overall.get('remaining_table_not_found')}",
        "",
        "## Per Ticker",
        "| Ticker | Source | Chunk | Evidence | Field Result | Remaining Blockers |",
        "|---|---|---|---|---|---|",
    ]
    for row in summary.get("ticker_results") or []:
        chunk = []
        if row.get("balance_sheet_chunk_found"):
            chunk.append("balance_sheet")
        if row.get("income_statement_chunk_found"):
            chunk.append("income_statement")
        fields = []
        for key in ("shareholders_equity_status", "revenue_status", "gross_profit_status"):
            if row.get(key):
                fields.append(f"{key.replace('_status', '')}:{row[key]}")
        lines.append(
            "| {ticker} | {source} | {chunk} | {evidence} | {fields} | {remaining} |".format(
                ticker=row.get("ticker"),
                source=row.get("source_id") or ("found" if row.get("source_found") else "missing"),
                chunk=", ".join(chunk) or "missing",
                evidence="linked" if row.get("evidence_linked") else "missing",
                fields=", ".join(fields) or "missing",
                remaining=", ".join(row.get("remaining_blockers") or []) or "-",
            )
        )
    lines.extend(["", "## Next Fixes", "| Ticker | Remaining Issue | Suggested Fix |", "|---|---|---|"])
    for row in summary.get("ticker_results") or []:
        remaining = row.get("remaining_blockers") or []
        if remaining:
            lines.append(f"| {row.get('ticker')} | {', '.join(remaining)} | recover source chunk or refine parser for remaining field |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 17 source chunk recovery summary")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--no-live", action="store_true")
    args = parser.parse_args()
    payload = compact_summary(build_payload(args.db_path, ["00700.HK", "300308.SZ", "688041.SH"], live=not args.no_live))
    if args.markdown:
        print(to_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run("build_phase17_source_chunk_recovery_summary.py", "success", "phase17 source chunk recovery summary built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
