#!/usr/bin/env python3
"""Persist Phase 28 semantic evidence candidates."""

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
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_semantic_evidence_persistence import (
    build_semantic_evidence_candidates,
    flatten_candidates,
    write_semantic_evidence_candidates,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "persist_semantic_evidence_candidates.py"


def build_payload(conn: sqlite3.Connection, *, tickers: str | None = None, mode: str = "dry_run") -> dict:
    candidate_payload = build_semantic_evidence_candidates(conn, tickers, use_real_sources=True, allow_mock_fallback=True, mode="mock")
    candidates = flatten_candidates(candidate_payload)
    written = write_semantic_evidence_candidates(conn, candidates) if mode == "execute" else 0
    return {
        "generated_at": candidate_payload.get("generated_at"),
        "mode": mode,
        "summary": {
            **(candidate_payload.get("summary") or {}),
            "evidence_candidates_created": len(candidates),
            "evidence_candidates_written": written,
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "new_pending_created": 0,
        },
        "rows": [
            {
                "ticker": row.get("ticker"),
                "evidence_candidates": row.get("evidence_candidates"),
                "candidate_count": len(row.get("evidence_candidates") or []),
            }
            for row in candidate_payload.get("rows") or []
        ],
        "safety": {
            "raw_source_text_written": False,
            "semantic_evidence_direct_promotion": False,
            "paper_order_created": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist semantic evidence candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--tickers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, tickers=args.tickers, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase28_semantic_evidence_candidates", args.tickers or "supply_chain_pilot", mode, SCRIPT_NAME, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase28 semantic evidence candidates persisted", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
