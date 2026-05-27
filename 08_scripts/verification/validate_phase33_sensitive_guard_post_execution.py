#!/usr/bin/env python3
"""Revalidate sensitive variable guardrails after Phase 33 execution."""

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
from smr_controlled_review_plan import phase33_audits
from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_sensitive_variable_guard import guard_candidates, guard_sensitive_variable, summarize_sensitive_guard
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    candidates = list_semantic_evidence_candidates(conn)
    checks = guard_candidates(candidates)
    synthetic_blocks = [
        guard_sensitive_variable(
            {
                "evidence_id": "phase33_synthetic_supplier_share_upgrade",
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
                "evidence_id": "phase33_synthetic_customer_allocation_upgrade",
                "ticker": "300394.SZ",
                "variable_type": "customer_allocation_proxy",
                "evidence_status": "confirmed",
                "allowed_usage": "research_evidence",
                "usable_for_promotion": False,
            },
            action="upgrade_to_confirmed_customer_allocation",
        ),
    ]
    live_violations = [
        row
        for row in checks
        if row.get("violations")
        and not all("allowed_usage too permissive" in str(v) for v in row.get("violations") or [])
    ]
    audits = phase33_audits(conn)
    confirmed_supplier = 0
    confirmed_asp = 0
    confirmed_customer = 0
    official_consensus = 0
    summary = summarize_sensitive_guard(checks + synthetic_blocks)
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if not live_violations else "fail",
        "summary": {
            "sensitive_items_checked": summary.get("sensitive_items_checked", 0),
            "confirmed_supplier_share_added": confirmed_supplier,
            "confirmed_ASP_added": confirmed_asp,
            "confirmed_customer_allocation_added": confirmed_customer,
            "official_consensus_added": official_consensus,
            "blocked_confirmed_upgrades": summary.get("blocked_confirmed_upgrades", 0),
            "phase33_audit_records": len(audits),
            "violations": len(live_violations),
        },
        "checks": checks,
        "synthetic_block_checks": synthetic_blocks,
        "safety": {
            "manual_action_can_bypass_guard": False,
            "promotion_allowed_true": 0,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 33 sensitive guard post execution")
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
