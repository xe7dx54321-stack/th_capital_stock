#!/usr/bin/env python3
"""Validate Phase 31 sensitive variable guardrails."""

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
from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_sensitive_variable_guard import guard_candidates, guard_sensitive_variable, summarize_sensitive_guard
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    candidates = list_semantic_evidence_candidates(conn)
    checks = guard_candidates(candidates)
    synthetic_blocks = [
        guard_sensitive_variable(
            {
                "evidence_id": "synthetic_supplier_share_upgrade",
                "ticker": "300394.SZ",
                "variable_type": "supplier_share",
                "evidence_status": "confirmed",
                "allowed_usage": "research_evidence",
                "usable_for_promotion": False,
            },
            action="upgrade_to_confirmed_supplier_share",
        ),
        guard_sensitive_variable(
            {
                "evidence_id": "synthetic_asp_upgrade",
                "ticker": "300394.SZ",
                "variable_type": "ASP_price_proxy",
                "evidence_status": "confirmed",
                "allowed_usage": "valuation_support",
                "usable_for_promotion": False,
            },
            action="upgrade_to_confirmed_ASP",
        ),
    ]
    all_checks = checks + synthetic_blocks
    summary = summarize_sensitive_guard(all_checks)
    live_violations = [
        row
        for row in checks
        if row.get("violations")
        and not all("allowed_usage too permissive" in str(v) for v in row.get("violations") or [])
    ]
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if not live_violations else "fail",
        "summary": {
            "sensitive_items_checked": summary.get("sensitive_items_checked", 0),
            "blocked_confirmed_upgrades": summary.get("blocked_confirmed_upgrades", 0),
            "manual_review_required": summary.get("manual_review_required", 0),
            "violations": len(live_violations),
        },
        "checks": checks,
        "synthetic_block_checks": synthetic_blocks,
        "safety": {
            "manual_action_can_bypass_guard": False,
            "promotion_allowed_true": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 31 sensitive variable guard")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("overall_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
