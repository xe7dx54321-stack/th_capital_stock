#!/usr/bin/env python3
"""Validate Phase 40 research-review state after guarded actions."""

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
from smr_research_review_actions import FORBIDDEN_REVIEW_ACTIONS
from smr_research_review_audit import list_audit_records
from smr_research_review_lifecycle import list_lifecycles
from smr_specific_evidence_request import list_specific_evidence_requests
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict:
    audits = list_audit_records(conn, limit=500)
    lifecycles = list_lifecycles(conn)
    requests = list_specific_evidence_requests(conn)
    forbidden_violations = sum(1 for row in audits if row.get("action") in FORBIDDEN_REVIEW_ACTIONS)
    pending_created = sum(1 for row in audits if row.get("pending_created"))
    paper_order_created = sum(1 for row in audits if row.get("paper_order_created"))
    promotion_allowed_true = sum(1 for row in audits if row.get("promotion_allowed_after_action"))
    promotion_allowed_true += sum(1 for row in lifecycles if row.get("promotion_allowed"))
    summary = {
        "research_review_actions_executed": len(audits),
        "audit_records_written": len(audits),
        "specific_evidence_requests_created": len(requests),
        "pending_created": pending_created,
        "paper_order_created": paper_order_created,
        "promotion_allowed_true": promotion_allowed_true,
        "forbidden_action_violations": forbidden_violations,
    }
    ok = (
        summary["pending_created"] == 0
        and summary["paper_order_created"] == 0
        and summary["promotion_allowed_true"] == 0
        and summary["forbidden_action_violations"] == 0
    )
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if ok else "fail",
        "summary": summary,
        "safety": {
            "research_review_only": True,
            "pending_human_review_created": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 40 post-action research review state")
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
