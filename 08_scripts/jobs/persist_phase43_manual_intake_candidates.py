#!/usr/bin/env python3
"""Persist Phase 43 manual intake candidates under guarded constraints."""

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
from smr_manual_intake_candidate_generator import (
    build_candidate_generation_payload,
    list_manual_intake_candidates,
    write_manual_intake_candidates,
)
from smr_manual_intake_permission_guard import build_permission_audit
from smr_registry import register_snapshot
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "persist_phase43_manual_intake_candidates.py"


def _available_candidates(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    rows = list_manual_intake_candidates(conn, ticker=ticker)
    if rows:
        return rows
    generated = build_candidate_generation_payload(None, ticker=ticker, mode="dry_run")
    return (generated.get("manual_intake_candidate_generation") or {}).get("candidate_rows") or []


def build_payload(conn: sqlite3.Connection, *, ticker: str, mode: str = "dry_run") -> dict[str, Any]:
    if mode not in {"dry_run", "execute"}:
        raise ValueError(f"Unsupported mode: {mode}")
    ticker = normalize_ticker(ticker)
    candidates = _available_candidates(conn, ticker)
    audit_rows = (build_permission_audit(conn, ticker).get("permission_audit") or {}).get("audit_rows") or []
    passed_ids = {row.get("candidate_id") for row in audit_rows if row.get("permission_passed")}
    eligible = [candidate for candidate in candidates if candidate.get("candidate_id") in passed_ids and not candidate.get("usable_for_promotion")]
    written = 0
    duplicates = 0
    if mode == "execute":
        result = write_manual_intake_candidates(conn, eligible, mark_persisted=True)
        written = result["written"]
        duplicates = result["duplicates_skipped"]
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_intake_persistence": {
            "mode": mode,
            "candidates_available": len(candidates),
            "eligible_for_persistence": len(eligible),
            "candidates_written": written,
            "duplicates_skipped": duplicates,
            "rejection_records_written": 0,
            "usable_for_promotion_true": 0,
            "confirmed_variables_added": 0,
            "pending_created": 0,
            "paper_order_created": 0,
            "eligible_candidate_ids": [candidate.get("candidate_id") for candidate in eligible],
        },
        "safety": {
            "candidate_is_confirmed_evidence": False,
            "confirmed_variables_added": 0,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist Phase 43 manual intake candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default=TARGET_REVIEW_TICKER)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase43_manual_intake_persistence", args.ticker.upper(), mode, SCRIPT_NAME, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
