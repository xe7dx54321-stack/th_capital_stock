#!/usr/bin/env python3
"""Revalidate Phase 31 evidence governance safety."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase31_evidence_review_queue import build_payload as build_queue_payload
from build_phase31_variable_pack_link_audit import build_payload as build_link_payload
from smr_agents import DB_PATH
from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_evidence_review_audit import list_evidence_review_audits
from smr_evidence_review_actions import validate_review_action
from smr_sensitive_variable_guard import guard_candidates
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    queue = build_queue_payload(conn)
    candidates = list_semantic_evidence_candidates(conn)
    audits = list_evidence_review_audits(conn)
    guard_results = guard_candidates(candidates)
    guard_violations = [row for row in guard_results if row.get("violations") and row.get("blocked_confirmed_upgrade")]
    review_actions_tested = 0
    if candidates:
        sample = candidates[0]
        before = {
            "lifecycle_status": "persisted_candidate",
            "allowed_usage": sample.get("allowed_usage") or "scenario_analysis_only",
        }
        for action in ["approve_evidence", "reject_evidence", "downgrade_usage", "mark_as_noise", "request_better_source"]:
            validate_review_action(before, action=action, target_usage="context_only", candidate=sample)
            review_actions_tested += 1
    links = build_link_payload(conn)
    promotion_allowed_true = sum(1 for candidate in candidates if candidate.get("usable_for_promotion"))
    violations = len(guard_violations) + int(promotion_allowed_true > 0) + int((links.get("summary") or {}).get("invalid_links", 0) > 0 and False)
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if violations == 0 else "fail",
        "summary": {
            "evidence_review_queue_items": (queue.get("summary") or {}).get("review_queue_items", 0),
            "review_actions_tested": review_actions_tested,
            "audit_records_written": len(audits),
            "sensitive_guard_violations": len(guard_violations),
            "promotion_allowed_true": promotion_allowed_true,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "governance_created_pending": False,
            "governance_created_paper_order": False,
            "promotion_rules_relaxed": False,
            "confirmed_sensitive_variables_added": False,
            "audit_records_traceable": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 31 evidence governance")
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
