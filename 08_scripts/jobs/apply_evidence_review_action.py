#!/usr/bin/env python3
"""Apply a Phase 31 manual evidence review action."""

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
from smr_evidence_review_actions import ALLOWED_ACTIONS, FORBIDDEN_ACTIONS, apply_evidence_review_action
from smr_registry import register_snapshot
from smr_runlog import log_run

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "apply_evidence_review_action.py"


def build_payload(
    conn: sqlite3.Connection,
    *,
    evidence_id: str,
    action: str,
    reason: str | None = None,
    target_usage: str | None = None,
    actor: str = "human_or_system",
    mode: str = "dry_run",
) -> dict:
    return apply_evidence_review_action(
        conn,
        evidence_id=evidence_id,
        action=action,
        reason=reason,
        target_usage=target_usage,
        actor=actor,
        dry_run=mode != "execute",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Phase 31 evidence review action")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--evidence-id", required=True)
    parser.add_argument("--action", required=True, choices=sorted(ALLOWED_ACTIONS | FORBIDDEN_ACTIONS))
    parser.add_argument("--reason")
    parser.add_argument("--target-usage")
    parser.add_argument("--actor", default="human_or_system")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(
            conn,
            evidence_id=args.evidence_id,
            action=args.action,
            reason=args.reason,
            target_usage=args.target_usage,
            actor=args.actor,
            mode=mode,
        )
        register_snapshot(
            conn,
            entity_type="phase31_evidence_review_action",
            entity_id=args.evidence_id,
            status=mode,
            source=SCRIPT_NAME,
            payload=payload,
        )
        if mode == "execute" and payload.get("allowed"):
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase31 evidence review action processed", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
