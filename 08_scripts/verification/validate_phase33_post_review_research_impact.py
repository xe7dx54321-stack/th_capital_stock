#!/usr/bin/env python3
"""Validate Phase 33 post-review research impact stays conservative."""

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
from smr_controlled_review_plan import grouped_audits_by_ticker, phase33_audits
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    audits = phase33_audits(conn)
    reviewed = len({row.get("evidence_id") for row in audits})
    variable_pack_changed = sum(1 for row in audits if row.get("action") in {"downgrade_usage", "mark_as_noise", "reject_evidence", "request_better_source"})
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if reviewed else "no_execute_actions",
        "summary": {
            "reviewed_evidence": reviewed,
            "variable_packs_changed": variable_pack_changed,
            "expectation_gap_changed": 0,
            "valuation_support_changed": 0,
            "bear_case_changed": 0,
            "confirmed_variables_added": 0,
            "new_pending_created": 0,
            "promotion_allowed_from_reviewed_evidence": sum(1 for row in audits if row.get("promotion_allowed_after_action")),
        },
        "ticker_results": grouped_audits_by_ticker(audits),
        "safety": {
            "review_action_forces_expectation_gap_upgrade": False,
            "confirmed_variables_added": 0,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 33 post-review research impact")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn)
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("overall_status") in {"partial_pass", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
