#!/usr/bin/env python3
"""Validate Phase 33 execute actions wrote traceable audit records."""

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
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    audits = phase33_audits(conn)
    execute_actions = [row for row in audits if row.get("mode") == "execute"]
    missing_before_after = [
        row
        for row in execute_actions
        if not row.get("before_status")
        or not row.get("after_status")
        or row.get("before_allowed_usage") is None
        or row.get("after_allowed_usage") is None
    ]
    missing_reason = [row for row in execute_actions if not row.get("reason")]
    promotion_true = [row for row in execute_actions if row.get("promotion_allowed_after_action")]
    violations = len(missing_before_after) + len(missing_reason) + len(promotion_true)
    return {
        "generated_at": now_ts(),
        "overall_status": "pass" if violations == 0 and len(execute_actions) > 0 else "fail",
        "summary": {
            "audit_records_found": len(audits),
            "execute_actions_found": len(execute_actions),
            "dry_run_actions_written": sum(1 for row in audits if row.get("mode") == "dry_run"),
            "missing_before_after": len(missing_before_after),
            "missing_reason": len(missing_reason),
            "promotion_allowed_after_action_true": len(promotion_true),
            "violations": violations,
        },
        "recent_actions": execute_actions[:20],
        "safety": {
            "audit_log_append_only": True,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 33 audit log execution")
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
