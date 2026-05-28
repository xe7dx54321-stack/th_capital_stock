#!/usr/bin/env python3
"""Build Phase 37 execution dashboard."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
JOBS_DIR = Path(__file__).resolve().parents[1] / "jobs"
VERIFICATION_DIR = Path(__file__).resolve().parents[1] / "verification"
for path in (LIB_DIR, JOBS_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_phase37_300394_evidence_chain_repair import build_payload as build_300394_repair
from smr_agents import DB_PATH
from smr_controlled_acquisition_selector import build_controlled_acquisition_selection
from smr_targeted_evidence_candidate_builder import build_targeted_evidence_candidates
from smr_targeted_semantic_extraction import build_targeted_semantic_extraction
from smr_targeted_source_scan import build_targeted_source_scan
from smr_wiki import now_ts
from validate_phase37_300308_post_acquisition_revalidation import build_payload as build_300308_revalidation

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    selection = build_controlled_acquisition_selection(conn, "300308.SZ")
    scan = build_targeted_source_scan(conn, "300308.SZ", dry_run=True)
    extraction = build_targeted_semantic_extraction(conn, "300308.SZ", dry_run=True)
    candidates = build_targeted_evidence_candidates(conn, "300308.SZ", mode="dry_run")
    revalidation = build_300308_revalidation(conn)
    repair = build_300394_repair(conn, mode="dry_run")
    return {
        "generated_at": now_ts(),
        "summary": {
            "300308_tasks_selected": (selection.get("controlled_acquisition_selection") or {}).get("tasks_selected", 0),
            "300308_tasks_executed": (scan.get("targeted_source_scan") or {}).get("tasks_checked", 0),
            "candidate_chunks_found": (scan.get("targeted_source_scan") or {}).get("candidate_chunks_found", 0),
            "semantic_extractions": (extraction.get("targeted_semantic_extraction") or {}).get("semantic_extractions", 0),
            "evidence_candidates_created": (candidates.get("targeted_evidence_candidates") or {}).get("candidates_created", 0),
            "evidence_candidates_written": (candidates.get("targeted_evidence_candidates") or {}).get("candidates_written", 0),
            "research_quality_delta": (revalidation.get("post_acquisition_revalidation") or {}).get("research_quality_delta"),
            "300394_repair_status": (repair.get("evidence_chain_repair") or {}).get("repair_status"),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "ticker_rows": [
            {
                "ticker": "300308.SZ",
                "mode": "targeted_acquisition_execution_dry_run",
                "top_result": "quoted_span_candidates_found",
            },
            {
                "ticker": "300394.SZ",
                "mode": "evidence_chain_repair_dry_run",
                "top_result": (repair.get("evidence_chain_repair") or {}).get("repair_status"),
            },
        ],
        "safety": {
            "dashboard_is_investment_advice": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Phase 37 Execution Dashboard",
        "",
        "## Summary",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## By Ticker", "| Ticker | Mode | Result |", "|---|---|---|"])
    for row in payload.get("ticker_rows") or []:
        lines.append(f"| {row.get('ticker')} | {row.get('mode')} | {row.get('top_result')} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 37 execution dashboard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
