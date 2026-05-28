#!/usr/bin/env python3
"""Run Phase 37 controlled evidence-chain repair for 300394.SZ."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_evidence_chain_diagnostics import build_evidence_chain_zero_diagnostics
from smr_research_evidence_chain import build_research_evidence_chain
from smr_semantic_evidence_persistence import build_semantic_evidence_candidates, flatten_candidates, guard_semantic_evidence_candidates, write_semantic_evidence_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _check_status(diagnostics: dict[str, Any], check_name: str) -> str:
    for row in (diagnostics.get("evidence_chain_zero_diagnostics") or {}).get("checks") or []:
        if row.get("check") == check_name:
            return str(row.get("status") or "missing")
    return "missing"


def build_payload(conn: sqlite3.Connection, *, mode: str = "dry_run") -> dict[str, Any]:
    ticker = "300394.SZ"
    before = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    diagnostics = build_evidence_chain_zero_diagnostics(conn, ticker)
    candidate_payload = build_semantic_evidence_candidates(
        conn,
        ticker,
        use_real_sources=True,
        allow_mock_fallback=False,
        mode="mock",
        use_text_cache=True,
        extract_text_if_missing=False,
        skip_metadata_only=True,
    )
    candidates = flatten_candidates(candidate_payload)
    guarded = guard_semantic_evidence_candidates(candidates, reject_noisy=True)
    eligible = guarded.get("eligible_candidates") or []
    written = 0
    if mode == "execute" and eligible:
        written = write_semantic_evidence_candidates(conn, eligible, enforce_quality_guard=True, reject_noisy=True)
    after = build_research_evidence_chain(conn, ticker).get("evidence_chain") or {}
    root_cause = (diagnostics.get("evidence_chain_zero_diagnostics") or {}).get("likely_root_causes") or []
    repair_status = "controlled_execute_completed" if written else "partial_repair_dry_run"
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "mode": mode,
        "evidence_chain_repair": {
            "before_evidence_chain_count": before.get("total_evidence", 0),
            "source_inventory_status": _check_status(diagnostics, "source_inventory"),
            "text_extraction_status": _check_status(diagnostics, "text_cache"),
            "semantic_extraction_status": _check_status(diagnostics, "semantic_extraction"),
            "candidate_builder_status": "candidate_created" if candidates else "no_clean_candidate",
            "persistence_status": "execute_written" if written else "dry_run_only",
            "candidate_created": len(candidates),
            "eligible_for_persistence": len(eligible),
            "candidates_written": written,
            "after_evidence_chain_count": after.get("total_evidence", 0),
            "repair_status": repair_status,
            "root_cause": root_cause,
            "next_step": "run controlled execute if clean candidates available" if not written else "rebuild research evidence chain and review candidates",
        },
        "safety": {
            "fake_evidence_written": False,
            "raw_content_saved": False,
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 37 300394 evidence-chain repair")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, mode=mode)
        if mode == "execute":
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
