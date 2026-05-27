#!/usr/bin/env python3
"""Run Phase 32 batch evidence review action dry-runs without writing state."""

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
from smr_evidence_review_workbench import build_workbench, dry_run_workbench_actions, filter_workbench_items
from smr_runlog import log_run
from smr_wiki import now_ts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_NAME = "run_phase32_batch_review_dry_run.py"


def build_payload(
    conn: sqlite3.Connection,
    *,
    priority: str | None = None,
    sensitive_only: bool = False,
    limit: int | None = None,
    ticker: str | None = None,
    evidence_id: str | None = None,
) -> dict:
    workbench = build_workbench(conn, ticker=ticker)
    items = filter_workbench_items(workbench.get("items") or [], priority=priority, sensitive_only=sensitive_only, limit=limit)
    if evidence_id:
        items = [item for item in workbench.get("items") or [] if item.get("evidence_id") == evidence_id]
    dry_run = dry_run_workbench_actions(conn, items)
    return {
        "generated_at": now_ts(),
        "filters": {"priority": priority, "sensitive_only": sensitive_only, "limit": limit, "ticker": ticker, "evidence_id": evidence_id},
        **dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 32 batch review dry-run")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--priority")
    parser.add_argument("--sensitive-only", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ticker")
    parser.add_argument("--evidence-id")
    parser.add_argument("--dry-run", action="store_true", help="Accepted for explicit safety; this job is always dry-run.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(
            conn,
            priority=args.priority,
            sensitive_only=args.sensitive_only,
            limit=args.limit,
            ticker=args.ticker,
            evidence_id=args.evidence_id,
        )
        conn.rollback()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase32 batch review dry-run complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
