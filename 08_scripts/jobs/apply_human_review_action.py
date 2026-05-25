#!/usr/bin/env python3
"""Apply a structured human review action to a pending recommendation."""

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
from smr_human_review_workflow import apply_human_review_action
from smr_registry import register_snapshot
from smr_runlog import log_run


SCRIPT_NAME = "apply_human_review_action.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply human review action to a recommendation")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--recommendation-id", required=True)
    parser.add_argument("--action", required=True, choices=[
        "approve_paper",
        "reject",
        "downgrade",
        "request_more_research",
        "reduce_position_size",
        "archive",
    ])
    parser.add_argument("--reviewer", default="manual")
    parser.add_argument("--note", required=True)
    parser.add_argument("--new-position-pct", type=float)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    dry_run = not args.execute
    conn = sqlite3.connect(args.db_path)
    try:
        result = apply_human_review_action(
            conn,
            recommendation_id=args.recommendation_id,
            action=args.action,
            reviewer=args.reviewer,
            note=args.note,
            new_position_pct=args.new_position_pct,
            dry_run=dry_run,
        )
        register_snapshot(
            conn,
            entity_type="human_review_action",
            entity_id=args.recommendation_id,
            status="dry_run" if dry_run else str(result.get("after_status") or "updated"),
            source=SCRIPT_NAME,
            payload=result,
        )
        if dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "human review action processed", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
